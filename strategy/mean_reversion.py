from typing import Dict, Any, List
import pandas as pd
from sqlalchemy.orm import Session
from strategy.base_strategy import BaseStrategy
from strategy.indicator_manager import IndicatorManager
from broker.kite_client import KiteClient
from broker.order_manager import OrderManager
from engine.risk_manager import RiskManager
from engine.position_manager import PositionManager
from database.models import TransactionType, OrderType, ProductType
from config.logging_config import get_logger

logger = get_logger("strategy")


class MeanReversionStrategy(BaseStrategy):
    """
    RSI Overbought/Oversold Reversion Strategy.
    Buys when RSI < 30 (oversold) and Sells when RSI > 70 (overbought).
    """

    def __init__(
        self,
        db: Session,
        kite_client: KiteClient,
        order_manager: OrderManager,
        risk_manager: RiskManager,
        position_manager: PositionManager,
        watchlist: Dict[str, int],
        rsi_period: int = 14,
        oversold: float = 30.0,
        overbought: float = 70.0,
        quantity: int = 10
    ):
        super().__init__(
            name="MeanReversion_Strategy",
            db=db,
            kite_client=kite_client,
            order_manager=order_manager,
            risk_manager=risk_manager,
            position_manager=position_manager
        )
        self.watchlist = watchlist
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
        self.quantity = quantity
        self.price_series: Dict[str, List[float]] = {s: [] for s in watchlist.keys()}

    def start(self) -> None:
        self.is_active = True
        logger.info(f"{self.name} started.")

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

            prices = self.price_series[symbol]
            prices.append(ltp)

            if len(prices) > 100:
                prices.pop(0)

            if len(prices) < self.rsi_period + 5:
                continue

            df = pd.DataFrame({"close": prices})
            rsi_series = IndicatorManager.calculate_rsi(df, period=self.rsi_period)
            latest_rsi = rsi_series.iloc[-1]

            if latest_rsi <= self.oversold:
                self._place_order(symbol, ltp, TransactionType.BUY)
            elif latest_rsi >= self.overbought:
                self._place_order(symbol, ltp, TransactionType.SELL)

    def _place_order(self, symbol: str, price: float, tx_type: TransactionType) -> None:
        is_valid, _ = self.risk_manager.validate_order(symbol, self.quantity, price, tx_type.value)
        if is_valid:
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
            except Exception as e:
                logger.error(f"MeanReversion order execution error: {str(e)}")
