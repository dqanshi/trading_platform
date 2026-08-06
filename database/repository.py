from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from database.models import User, Order, Position, Trade, SystemConfig, AuditLog
from utils.constants import OrderStatus


class Repository:
    """
    Unified database repository for executing CRUD operations across trading entities.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    def create_order(self, order_data: Dict[str, Any]) -> Order:
        order = Order(**order_data)
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

    def update_order_status(
        self,
        order_id: str,
        status: OrderStatus,
        avg_price: float = 0.0,
        rejection_reason: Optional[str] = None
    ) -> Optional[Order]:
        order = self.db.query(Order).filter(Order.order_id == order_id).first()
        if order:
            order.status = status.value
            if avg_price > 0:
                order.average_price = avg_price
            if rejection_reason:
                order.rejection_reason = rejection_reason
            self.db.commit()
            self.db.refresh(order)
        return order

    def update_or_create_position(
        self,
        symbol: str,
        exchange: str,
        product: str,
        qty_change: int,
        price: float
    ) -> Position:
        pos = self.db.query(Position).filter(Position.symbol == symbol).first()
        if not pos:
            pos = Position(
                symbol=symbol,
                exchange=exchange,
                product=product,
                quantity=qty_change,
                average_price=price
            )
            self.db.add(pos)
        else:
            new_qty = pos.quantity + qty_change
            if new_qty == 0:
                pos.quantity = 0
                pos.average_price = 0.0
            else:
                if (pos.quantity > 0 and qty_change > 0) or (pos.quantity < 0 and qty_change < 0):
                    total_cost = (pos.quantity * pos.average_price) + (qty_change * price)
                    pos.average_price = total_cost / new_qty
                pos.quantity = new_qty
        self.db.commit()
        self.db.refresh(pos)
        return pos

    def log_trade(self, trade_data: Dict[str, Any]) -> Trade:
        trade = Trade(**trade_data)
        self.db.add(trade)
        self.db.commit()
        self.db.refresh(trade)
        return trade

    def add_audit_log(self, module: str, message: str, level: str = "INFO"):
        log_entry = AuditLog(module=module, message=message, level=level)
        self.db.add(log_entry)
        self.db.commit()
