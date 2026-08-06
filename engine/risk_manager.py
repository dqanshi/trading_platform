from typing import Tuple, Dict, Any
from sqlalchemy.orm import Session
from database.models import Position, OrderStatus
from config.config import settings
from config.logging_config import get_logger

logger = get_logger("risk")


class RiskManager:
    """
    Enforces risk checks including max trade order value, daily stop loss limits, and position caps.
    """

    def __init__(self, db: Session):
        self.db = db
        self.max_order_value = settings.MAX_ORDER_VALUE
        self.max_daily_loss = settings.MAX_DAILY_LOSS
        self.max_open_positions = settings.MAX_OPEN_POSITIONS
        self.is_kill_switch_active = False

    def check_kill_switch() -> bool:
        return self.is_kill_switch_active

    def trigger_kill_switch(self):
        self.is_kill_switch_active = True
        logger.critical("RISK KILL SWITCH ACTIVATED! All new trade entries are blocked.")

    def validate_order(
        self,
        symbol: str,
        quantity: int,
        price: float,
        transaction_type: str
    ) -> Tuple[bool, str]:

        if self.is_kill_switch_active:
            return False, "Order rejected: Risk Kill Switch is ACTIVE."

        order_value = quantity * price
        if order_value > self.max_order_value:
            return False, f"Order value ₹{order_value:,.2f} exceeds max limit of ₹{self.max_order_value:,.2f}."

        open_positions = self.db.query(Position).filter(Position.quantity != 0).all()
        pos_symbols = [p.symbol for p in open_positions]

        if symbol not in pos_symbols and len(open_positions) >= self.max_open_positions:
            return False, f"Maximum open positions limit ({self.max_open_positions}) reached."

        total_unrealized_loss = sum(p.m2m for p in open_positions if p.m2m < 0)
        if abs(total_unrealized_loss) >= self.max_daily_loss:
            self.trigger_kill_switch()
            return False, f"Total daily loss ₹{abs(total_unrealized_loss):,.2f} hit max daily loss threshold ₹{self.max_daily_loss:,.2f}."

        return True, "Order passed risk checks."
