from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from strategy.base_strategy import BaseStrategy
from broker.kite_client import KiteClient
from broker.order_manager import OrderManager
from engine.risk_manager import RiskManager
from engine.position_manager import PositionManager
from database.models import TransactionType, OrderType, ProductType
from config.logging_config import get_logger

logger = get_logger("strategy")


class BreakoutStrategy(BaseStrategy):
    """
    20-period High/Low Channel Breakout Strategy.
    """

    def __init__(
        self,
        db: Session,
        kite_client: KiteClient,
        order_manager: OrderManager,
        risk_manager: RiskManager,
        position_manager: PositionManager,
        watchlist: Dict[str, int],
        lookback_period: int = 20,
        quantity: int = 5
    ):
        super().__init__(
            name="Breakout_Strategy",
            db=db,
            kite_client=kite_client,
            order_manager=order_manager,
            risk_manager=risk_manager,
            position_manager=position_manager
        )
        self.watchlist = watchlist
        self.lookback_period = lookback_period
        self.quantity = quantity
        self.price_history: Dict[str, List[float]] = {s: [] for s in watchlist.keys()}

    def start(self) -> None:
        self.is_active = True
        logger.info(f"{self.name} activated for watchlist: {list(self.watchlist.keys())}")

    def stop(self) -> None:
        self.is_active = False
        logger.info(f"{self.name} stopped.")

    def on_tick(self, ticks: List[Dict[str, Any]]) -> None:
        if not self.is_active:
            return

        for tick in ticks:
            symbol = tick.get("tradingsymbol")
            ltp = tick.get("last_price")

            if not symbol or not ltp or symbol not in self.watchlist:
                continue

            history = self.price_history[symbol]
            history.append(ltp)

            if len(history) > self.lookback_period:
                history.pop(0)

            if len(history) < self.lookback_period:
                continue

            channel_high = max(history[:-1])
            channel_low = min(history[:-1])

            if ltp > channel_high:
                self._execute(symbol, ltp, TransactionType.BUY)
            elif ltp < channel_low:
                self._execute(symbol, ltp, TransactionType.SELL)

    def _execute(self, symbol: str, price: float, tx_type: TransactionType) -> None:
        is_valid, reason = self.risk_manager.validate_order(
            symbol=symbol, quantity=self.quantity, price=price, transaction_type=tx_type.value
        )
        if not is_valid:
            return

        try:
            self.order_manager.execute_order(
                symbol=symbol,
                exchange="NSE",
                transaction_type=tx_type,
                order_type=OrderType.MARKET,
                product=ProductType.MIS,
                quantity=self.quantity,
                price=price,
                strategy_name=self.name
            )
            logger.info(f"{self.name} triggered {tx_type.value} for {symbol} at {price}")
        except Exception as e:
            logger.error(f"Breakout order failed for {symbol}: {str(e)}")
