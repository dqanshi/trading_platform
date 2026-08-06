from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from broker.order_manager import OrderManager
from database.models import Order, TransactionType, OrderType, ProductType, OrderStatus
from utils.exceptions import OrderExecutionError
from config.logging_config import get_logger

logger = get_logger("system")


class OrderExecutor:
    """
    Dedicated transactional order placement engine handling validation, retries, and persistence.
    """

    def __init__(self, order_manager: OrderManager, db: Session):
        self.order_manager = order_manager
        self.db = db

    def place_market_order(
        self,
        symbol: str,
        transaction_type: TransactionType,
        quantity: int,
        strategy_name: Optional[str] = None
    ) -> Order:
        try:
            return self.order_manager.execute_order(
                symbol=symbol,
                exchange="NSE",
                transaction_type=transaction_type,
                order_type=OrderType.MARKET,
                product=ProductType.MIS,
                quantity=quantity,
                strategy_name=strategy_name
            )
        except Exception as e:
            logger.error(f"Market order execution failed for {symbol}: {str(e)}")
            raise OrderExecutionError(f"Failed to execute market order for {symbol}: {str(e)}")

    def place_limit_order(
        self,
        symbol: str,
        transaction_type: TransactionType,
        quantity: int,
        price: float,
        strategy_name: Optional[str] = None
    ) -> Order:
        try:
            return self.order_manager.execute_order(
                symbol=symbol,
                exchange="NSE",
                transaction_type=transaction_type,
                order_type=OrderType.LIMIT,
                product=ProductType.MIS,
                quantity=quantity,
                price=price,
                strategy_name=strategy_name
            )
        except Exception as e:
            logger.error(f"Limit order execution failed for {symbol}: {str(e)}")
            raise OrderExecutionError(f"Failed to execute limit order for {symbol}: {str(e)}")
