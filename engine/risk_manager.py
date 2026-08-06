from datetime import datetime, time
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from config.config import settings
from database.repository import TradeRepository, PositionRepository
from broker.kite_client import KiteClient
from config.logging_config import get_logger

logger = get_logger("system")


class RiskManager:
    """
    Risk Management module responsible for validating orders against pre-defined risk criteria,
    monitoring daily limits, managing circuit breakers, and enforcing trading time windows.
    """

    def __init__(self, db: Session, kite_client: Optional[KiteClient] = None):
        self.db = db
        self.kite_client = kite_client
        self.trade_repo = TradeRepository(db)
        self.position_repo = PositionRepository(db)
        self.consecutive_failures: int = 0
        self.circuit_broken: bool = False

    def is_within_trading_window(self) -> bool:
        current_time = datetime.now().time()
        start_time = settings.get_parsed_trading_start()
        end_time = settings.get_parsed_trading_end()
        return start_time <= current_time <= end_time

    def register_failure() -> None:
        self.consecutive_failures += 1
        logger.warning(f"Consecutive order execution failure registered. Count: {self.consecutive_failures}")
        if self.consecutive_failures >= settings.MAX_REPEATED_FAILURES:
            self.circuit_broken = True
            logger.error(
                f"Circuit breaker tripped! Consecutive failures reached threshold: "
                f"{self.consecutive_failures}/{settings.MAX_REPEATED_FAILURES}"
            )

    def reset_failures() -> None:
        self.consecutive_failures = 0
        self.circuit_broken = False

    def calculate_daily_pnl(self) -> float:
        trades = self.trade_repo.get_todays_trades()
        realized_pnl = sum(t.pnl for t in trades)

        active_positions = self.position_repo.get_active_positions()
        unrealized_pnl = sum(p.m2m for p in active_positions)

        return realized_pnl + unrealized_pnl

    def validate_order(
        self,
        symbol: str,
        quantity: int,
        price: float,
        transaction_type: str
    ) -> Tuple[bool, str]:
        """
        Validates whether a proposed order complies with all active risk management rules.
        """
        if self.circuit_broken:
            return False, "Circuit breaker active due to consecutive system failures"

        if not self.is_within_trading_window():
            return False, f"Current time is outside the designated trading window ({settings.TRADING_WINDOW_START} - {settings.TRADING_WINDOW_END})"

        daily_trades_count = self.trade_repo.get_daily_trade_count()
        if daily_trades_count >= settings.MAX_TRADES_PER_DAY:
            return False, f"Maximum daily trade limit reached ({daily_trades_count}/{settings.MAX_TRADES_PER_DAY})"

        current_pnl = self.calculate_daily_pnl()
        if current_pnl <= -abs(settings.MAX_DAILY_LOSS):
            return False, f"Maximum daily loss breach threshold hit (Current PnL: {current_pnl:.2f}, Limit: -{settings.MAX_DAILY_LOSS:.2f})"

        order_value = quantity * price
        if order_value > settings.MAX_POSITION_SIZE:
            return False, f"Order value ({order_value:.2f}) exceeds maximum allowed position size ({settings.MAX_POSITION_SIZE:.2f})"

        existing_pos = self.position_repo.get_by_symbol(symbol)
        if existing_pos and existing_pos.is_open:
            if (transaction_type == "BUY" and existing_pos.quantity > 0) or (transaction_type == "SELL" and existing_pos.quantity < 0):
                new_total_value = abs(existing_pos.quantity + (quantity if transaction_type == "BUY" else -quantity)) * price
                if new_total_value > settings.MAX_POSITION_SIZE:
                    return False, f"Aggregated position size ({new_total_value:.2f}) would exceed limit ({settings.MAX_POSITION_SIZE:.2f})"

        if self.kite_client:
            try:
                margins = self.kite_client.get_margins()
                available_cash = margins.get("equity", {}).get("available", {}).get("live_balance", 0.0)
                if available_cash > 0 and order_value > available_cash:
                    return False, f"Insufficient margin: Required {order_value:.2f}, Available {available_cash:.2f}"
            except Exception as e:
                logger.error(f"Failed to fetch margin context during risk validation: {str(e)}")

        return True, "Order risk checks passed successfully"
