from datetime import datetime, time
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from strategy.base_strategy import BaseStrategy
from broker.kite_client import KiteClient
from broker.order_manager import OrderManager
from engine.risk_manager import RiskManager
from engine.position_manager import PositionManager
from database.models import TransactionType, OrderType, ProductType
from config.logging_config import get_logger

logger = get_logger("strategy")


class ORBInstrumentState:
    def __init__(self, symbol: str, instrument_token: int):
        self.symbol = symbol
        self.instrument_token = instrument_token
        self.orb_high: float = 0.0
        self.orb_low: float = float("inf")
        self.range_established: bool = False
        self.traded_today: bool = False


class ORBStrategy(BaseStrategy):
    """
    Opening Range Breakout (ORB) Strategy.
    Calculates the High and Low prices during the first N minutes (e.g., 09:15 - 09:30)
    and executes BUY on upside breakout or SELL on downside breakout.
    """

    def __init__(
        self,
        db: Session,
        kite_client: KiteClient,
        order_manager: OrderManager,
        risk_manager: RiskManager,
        position_manager: PositionManager,
        watchlist: Dict[str, int],
        range_start_time: str = "09:15",
        range_end_time: str = "09:30",
        quantity_per_trade: int = 10
    ):
        super().__init__(
            name="ORB_Strategy",
            db=db,
            kite_client=kite_client,
            order_manager=order_manager,
            risk_manager=risk_manager,
            position_manager=position_manager
        )
        self.watchlist = watchlist
        self.range_start_time = self._parse_time(range_start_time)
        self.range_end_time = self._parse_time(range_end_time)
        self.quantity_per_trade = quantity_per_trade
        self.instruments: Dict[str, ORBInstrumentState] = {
            symbol: ORBInstrumentState(symbol, token)
            for symbol, token in watchlist.items()
        }

    def _parse_time(self, time_str: str) -> time:
        h, m = map(int, time_str.split(":"))
        return time(h, m)

    def start(self) -> None:
        self.is_active = True
        logger.info(f"{self.name} started with watchlist: {list(self.watchlist.keys())}")

    def stop(self) -> None:
        self.is_active = False
        logger.info(f"{self.name} stopped.")

    def on_tick(self, ticks: List[Dict[str, Any]]) -> None:
        if not self.is_active:
            return

        current_time = datetime.now().time()

        for tick in ticks:
            symbol = tick.get("tradingsymbol")
            ltp = tick.get("last_price")

            if not symbol or not ltp or symbol not in self.instruments:
                continue

            state = self.instruments[symbol]

            # Phase 1: Build Opening Range
            if self.range_start_time <= current_time < self.range_end_time:
                if ltp > state.orb_high:
                    state.orb_high = ltp
                if ltp < state.orb_low:
                    state.orb_low = ltp

            # Phase 2: Finalize Range
            elif current_time >= self.range_end_time and not state.range_established:
                if state.orb_high > 0 and state.orb_low < float("inf"):
                    state.range_established = True
                    logger.info(
                        f"ORB Range set for {symbol}: High={state.orb_high}, Low={state.orb_low}"
                    )

            # Phase 3: Monitor Breakouts
            elif current_time >= self.range_end_time and state.range_established and not state.traded_today:
                if ltp > state.orb_high:
                    self._execute_breakout(state, ltp, TransactionType.BUY)
                elif ltp < state.orb_low:
                    self._execute_breakout(state, ltp, TransactionType.SELL)

    def _execute_breakout(
        self,
        state: ORBInstrumentState,
        price: float,
        transaction_type: TransactionType
    ) -> None:
        tx_str = transaction_type.value
        is_valid, reason = self.risk_manager.validate_order(
            symbol=state.symbol,
            quantity=self.quantity_per_trade,
            price=price,
            transaction_type=tx_str
        )

        if not is_valid:
            logger.warning(f"ORB Breakout rejected by Risk Manager for {state.symbol}: {reason}")
            return

        try:
            order = self.order_manager.execute_order(
                symbol=state.symbol,
                exchange="NSE",
                transaction_type=transaction_type,
                order_type=OrderType.MARKET,
                product=ProductType.MIS,
                quantity=self.quantity_per_trade,
                price=price,
                strategy_name=self.name
            )
            state.traded_today = True
            logger.info(f"ORB {tx_str} Breakout trade executed for {state.symbol}. Order ID: {order.order_id}")
            self.risk_manager.reset_failures()
        except Exception as e:
            self.risk_manager.register_failure()
            logger.error(f"Failed to execute ORB breakout trade for {state.symbol}: {str(e)}")
