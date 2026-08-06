import uuid
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from broker.kite_client import KiteClient
from database.models import Order, TransactionType, OrderType, ProductType, OrderStatus
from database.repository import Repository
from utils.notifier import notifier
from config.logging_config import get_logger

logger = get_logger("broker")


class OrderManager:
    """
    Central router for processing orders, updating database records, and triggering notifications.
    """

    def __init__(self, kite_client: KiteClient, db: Optional[Session] = None):
        self.kite_client = kite_client
        self.db = db

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
        strategy_name: str = "MANUAL"
    ) -> Order:
        local_order_id = f"ORD_{uuid.uuid4().hex[:10].upper()}"

        order_data = {
            "order_id": local_order_id,
            "symbol": symbol.upper(),
            "exchange": exchange.upper(),
            "transaction_type": transaction_type.value,
            "order_type": order_type.value,
            "product": product.value,
            "quantity": quantity,
            "price": price,
            "trigger_price": trigger_price,
            "status": OrderStatus.SUBMITTED.value,
            "strategy_name": strategy_name
        }

        repo = Repository(self.db) if self.db else None
        order = repo.create_order(order_data) if repo else Order(**order_data)

        try:
            kite_order_id = self.kite_client.place_order(
                variety="regular",
                exchange=exchange,
                tradingsymbol=symbol,
                transaction_type=transaction_type.value,
                quantity=quantity,
                product=product.value,
                order_type=order_type.value,
                price=price if order_type in [OrderType.LIMIT, OrderType.SL] else None,
                trigger_price=trigger_price if order_type in [OrderType.SL, OrderType.SL_M] else None
            )

            if repo:
                repo.update_order_status(local_order_id, OrderStatus.OPEN, avg_price=price)
                repo.update_or_create_position(
                    symbol=symbol,
                    exchange=exchange,
                    product=product.value,
                    qty_change=quantity if transaction_type == TransactionType.BUY else -quantity,
                    price=price
                )

            notifier.notify_trade(symbol, transaction_type.value, quantity, price, kite_order_id)
            return order

        except Exception as e:
            logger.error(f"Order placement failed for {symbol}: {str(e)}")
            if repo:
                repo.update_order_status(local_order_id, OrderStatus.REJECTED, rejection_reason=str(e))
            raise e

    def cancel_order(self, order_id: str) -> bool:
        success = self.kite_client.cancel_order(variety="regular", order_id=order_id)
        if success and self.db:
            repo = Repository(self.db)
            repo.update_order_status(order_id, OrderStatus.CANCELLED)
        return success
