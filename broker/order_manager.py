from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from broker.kite_client import KiteClient
from database.repository import OrderRepository, TradeRepository, PositionRepository
from database.models import OrderStatus, TransactionType, OrderType, ProductType, Order
from config.logging_config import get_logger

logger = get_logger("orders")


class OrderManager:
    def __init__(self, kite_client: KiteClient, db: Session):
        self.kite_client = kite_client
        self.db = db
        self.order_repo = OrderRepository(db)
        self.trade_repo = TradeRepository(db)
        self.position_repo = PositionRepository(db)

    def execute_order(
        self,
        symbol: str,
        exchange: str,
        transaction_type: TransactionType,
        order_type: OrderType,
        product: ProductType,
        quantity: int,
        price: float = 0.0,
        trigger_price: float = 0.0,
        strategy_name: Optional[str] = None
    ) -> Order:
        order_record = self.order_repo.create({
            "order_id": f"PENDING_{int(logger.handlers[0].formatter.converter().timestamp() if hasattr(logger.handlers[0].formatter, 'converter') else 0)}",
            "symbol": symbol,
            "exchange": exchange,
            "transaction_type": transaction_type,
            "order_type": order_type,
            "product": product,
            "quantity": quantity,
            "filled_quantity": 0,
            "price": price,
            "trigger_price": trigger_price,
            "status": OrderStatus.OPEN,
            "strategy_name": strategy_name
        })

        try:
            kite_order_id = self.kite_client.place_order(
                symbol=symbol,
                exchange=exchange,
                transaction_type=transaction_type.value,
                quantity=quantity,
                order_type=order_type.value,
                product=product.value,
                price=price,
                trigger_price=trigger_price,
                tag=strategy_name
            )

            self.order_repo.update(order_record.id, {
                "order_id": kite_order_id,
                "status": OrderStatus.OPEN
            })
            return self.order_repo.get_by_id(order_record.id)

        except Exception as e:
            self.order_repo.update(order_record.id, {
                "status": OrderStatus.REJECTED,
                "status_message": str(e)
            })
            logger.error(f"Order submission failed for {symbol}: {str(e)}")
            raise e

    def cancel_order(self, order_id: str) -> bool:
        db_order = self.order_repo.get_by_order_id(order_id)
        if not db_order:
            raise ValueError(f"Order ID {order_id} not found in database")

        try:
            self.kite_client.cancel_order(order_id)
            self.order_repo.update(db_order.id, {"status": OrderStatus.CANCELLED})
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {str(e)}")
            raise e

    def sync_orders(self) -> List[Order]:
        try:
            remote_orders = self.kite_client.get_orders()
            updated_orders = []

            for r_order in remote_orders:
                db_order = self.order_repo.get_by_order_id(r_order["order_id"])
                if db_order:
                    status_str = r_order["status"].upper()
                    mapped_status = OrderStatus.OPEN
                    if status_str == "COMPLETE":
                        mapped_status = OrderStatus.COMPLETE
                    elif status_str == "REJECTED":
                        mapped_status = OrderStatus.REJECTED
                    elif status_str in ["CANCELLED", "CANCELED"]:
                        mapped_status = OrderStatus.CANCELLED
                    elif status_str == "TRIGGER PENDING":
                        mapped_status = OrderStatus.TRIGGER_PENDING

                    updated = self.order_repo.update(db_order.id, {
                        "exchange_order_id": r_order.get("exchange_order_id"),
                        "filled_quantity": r_order.get("filled_quantity", 0),
                        "status": mapped_status,
                        "status_message": r_order.get("status_message")
                    })
                    
                    if mapped_status == OrderStatus.COMPLETE and db_order.status != OrderStatus.COMPLETE:
                        self._process_completed_order(updated, r_order)
                    
                    updated_orders.append(updated)

            return updated_orders
        except Exception as e:
            logger.error(f"Order synchronization failed: {str(e)}")
            raise e

    def _process_completed_order(self, order: Order, remote_data: Dict[str, Any]) -> None:
        average_price = remote_data.get("average_price", order.price)
        trade_id = f"TRD_{order.order_id}"

        existing_trade = self.trade_repo.db.query(self.trade_repo.model).filter_by(trade_id=trade_id).first()
        if not existing_trade:
            self.trade_repo.create({
                "trade_id": trade_id,
                "order_id": order.id,
                "symbol": order.symbol,
                "exchange": order.exchange,
                "transaction_type": order.transaction_type,
                "quantity": order.quantity,
                "price": average_price,
                "pnl": 0.0,
                "strategy_name": order.strategy_name
            })

            is_buy = (order.transaction_type == TransactionType.BUY)
            self.position_repo.upsert_position(
                symbol=order.symbol,
                exchange=order.exchange,
                product=order.product,
                quantity=order.quantity,
                price=average_price,
                is_buy=is_buy
            )
