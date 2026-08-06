from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from broker.kite_client import KiteClient
from broker.order_manager import OrderManager
from database.repository import PositionRepository, TradeRepository
from database.models import Position, TransactionType, OrderType, ProductType
from config.config import settings
from config.logging_config import get_logger

logger = get_logger("strategy")


class PositionTracker:
    def __init__(self, position: Position):
        self.symbol: str = position.symbol
        self.quantity: int = position.quantity
        self.entry_price: float = position.buy_price if position.quantity > 0 else position.sell_price
        self.high_water_mark: float = self.entry_price
        self.low_water_mark: float = self.entry_price
        self.stop_loss: float = 0.0
        self.target: float = 0.0
        self.trailing_stop_loss: float = 0.0
        self._calculate_initial_stops()

    def _calculate_initial_stops((self) -> None:
        if self.quantity > 0:  # Long Position
            self.stop_loss = self.entry_price * (1.0 - (settings.SL_PERCENTAGE / 100.0))
            self.target = self.entry_price * (1.0 + (settings.TARGET_PERCENTAGE / 100.0))
            self.trailing_stop_loss = self.stop_loss
        elif self.quantity < 0:  # Short Position
            self.stop_loss = self.entry_price * (1.0 + (settings.SL_PERCENTAGE / 100.0))
            self.target = self.entry_price * (1.0 - (settings.TARGET_PERCENTAGE / 100.0))
            self.trailing_stop_loss = self.stop_loss

    def update_price(self, ltp: float) -> Optional[str]:
        """
        Updates peak prices and checks if SL, Target, or Trailing SL conditions are triggered.
        Returns the trigger reason if exit condition is met, else None.
        """
        if self.quantity > 0:  # Long Position
            if ltp > self.high_water_mark:
                self.high_water_mark = ltp
                if settings.TRAILING_SL_PERCENTAGE > 0:
                    new_trailing = ltp * (1.0 - (settings.TRAILING_SL_PERCENTAGE / 100.0))
                    if new_trailing > self.trailing_stop_loss:
                        self.trailing_stop_loss = new_trailing

            if ltp <= self.stop_loss:
                return "STOP_LOSS_HIT"
            if ltp <= self.trailing_stop_loss and self.trailing_stop_loss > self.stop_loss:
                return "TRAILING_STOP_LOSS_HIT"
            if ltp >= self.target:
                return "TARGET_HIT"

        elif self.quantity < 0:  # Short Position
            if ltp < self.low_water_mark:
                self.low_water_mark = ltp
                if settings.TRAILING_SL_PERCENTAGE > 0:
                    new_trailing = ltp * (1.0 + (settings.TRAILING_SL_PERCENTAGE / 100.0))
                    if new_trailing < self.trailing_stop_loss or self.trailing_stop_loss == 0.0:
                        self.trailing_stop_loss = new_trailing

            if ltp >= self.stop_loss:
                return "STOP_LOSS_HIT"
            if ltp >= self.trailing_stop_loss and self.trailing_stop_loss < self.stop_loss:
                return "TRAILING_STOP_LOSS_HIT"
            if ltp <= self.target:
                return "TARGET_HIT"

        return None


class PositionManager:
    """
    Position Manager monitors active positions, updates mark-to-market valuations in real-time,
    evaluates exit triggers (SL, Target, Trailing SL), and enforces End-of-Day square-offs.
    """

    def __init__(self, db: Session, order_manager: OrderManager):
        self.db = db
        self.order_manager = order_manager
        self.position_repo = PositionRepository(db)
        self.active_trackers: Dict[str, PositionTracker] = {}
        self._load_active_positions()

    def _load_active_positions(self) -> None:
        active_positions = self.position_repo.get_active_positions()
        for pos in active_positions:
            self.active_trackers[pos.symbol] = PositionTracker(pos)

    def on_tick(self, ticks: List[Dict[str, Any]]) -> None:
        """
        Processes real-time market data ticks, updates M2M, and checks stop loss/target limits.
        """
        for tick in ticks:
            symbol = tick.get("tradingsymbol")
            ltp = tick.get("last_price")
            if not symbol or not ltp:
                continue

            pos = self.position_repo.get_by_symbol(symbol)
            if pos and pos.is_open:
                # Update Mark-to-Market calculation
                if pos.quantity > 0:
                    pos.m2m = (ltp - pos.buy_price) * pos.quantity
                else:
                    pos.m2m = (pos.sell_price - ltp) * abs(pos.quantity)
                
                self.db.commit()

                # Evaluate Tracker logic
                if symbol not in self.active_trackers:
                    self.active_trackers[symbol] = PositionTracker(pos)

                tracker = self.active_trackers[symbol]
                trigger = tracker.update_price(ltp)
                
                if trigger:
                    logger.info(f"Exit trigger '{trigger}' fired for {symbol} at LTP {ltp}")
                    self.square_off_position(symbol, reason=trigger)

    def square_off_position(self, symbol: str, reason: str = "MANUAL_SQUARE_OFF") -> None:
        pos = self.position_repo.get_by_symbol(symbol)
        if not pos or not pos.is_open or pos.quantity == 0:
            logger.warning(f"No active position to square off for symbol {symbol}")
            return

        tx_type = TransactionType.SELL if pos.quantity > 0 else TransactionType.BUY
        qty = abs(pos.quantity)

        logger.info(f"Executing square-off for {symbol} | Quantity: {qty} | Reason: {reason}")
        
        self.order_manager.execute_order(
            symbol=pos.symbol,
            exchange=pos.exchange,
            transaction_type=tx_type,
            order_type=OrderType.MARKET,
            product=pos.product,
            quantity=qty,
            strategy_name=f"SQUARE_OFF_{reason}"
        )

        if symbol in self.active_trackers:
            del self.active_trackers[symbol]

    def square_off_all_positions(self, reason: str = "EOD_SQUARE_OFF") -> None:
        active_positions = self.position_repo.get_active_positions()
        logger.info(f"Initiating bulk square-off for {len(active_positions)} active positions. Reason: {reason}")
        
        for pos in active_positions:
            try:
                self.square_off_position(pos.symbol, reason=reason)
            except Exception as e:
                logger.error(f"Failed to square off position {pos.symbol}: {str(e)}")

    def check_eod_square_off(self) -> None:
        current_time = datetime.now().time()
        square_off_time = settings.get_parsed_square_off_time()
        
        if current_time >= square_off_time:
            active_positions = self.position_repo.get_active_positions()
            if active_positions:
                logger.info(f"EOD trigger time reached ({settings.SQUARE_OFF_TIME}). Squaring off open positions.")
                self.square_off_all_positions(reason="SCHEDULED_EOD")
