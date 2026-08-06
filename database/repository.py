from datetime import datetime, date
from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, func
from database.session import Base
from database.models import (
    User, Order, Trade, Position, Report, SystemSettings, SystemLog, OrderStatus
)

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Generic repository providing standard CRUD database operations."""

    def __init__(self, model: Type[T], db: Session):
        self.model = model
        self.db = db

    def get_by_id(self, item_id: int) -> Optional[T]:
        return self.db.get(self.model, item_id)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        stmt = select(self.model).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def create(self, obj_in: Dict[str, Any]) -> T:
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, item_id: int, obj_in: Dict[str, Any]) -> Optional[T]:
        db_obj = self.get_by_id(item_id)
        if db_obj:
            for field, value in obj_in.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj

    def delete(self, item_id: int) -> bool:
        db_obj = self.get_by_id(item_id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
            return True
        return False


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_username(self, username: str) -> Optional[User]:
        stmt = select(User).where(User.username == username)
        return self.db.scalars(stmt).first()

    def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        return self.db.scalars(stmt).first()


class OrderRepository(BaseRepository[Order]):
    def __init__(self, db: Session):
        super().__init__(Order, db)

    def get_by_order_id(self, order_id: str) -> Optional[Order]:
        stmt = select(Order).where(Order.order_id == order_id)
        return self.db.scalars(stmt).first()

    def get_todays_orders(self) -> List[Order]:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        stmt = select(Order).where(Order.created_at >= today_start).order_by(Order.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def get_open_orders(self) -> List[Order]:
        stmt = select(Order).where(Order.status.in_([OrderStatus.OPEN, OrderStatus.TRIGGER_PENDING]))
        return list(self.db.scalars(stmt).all())


class TradeRepository(BaseRepository[Trade]):
    def __init__(self, db: Session):
        super().__init__(Trade, db)

    def get_todays_trades(self) -> List[Trade]:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        stmt = select(Trade).where(Trade.executed_at >= today_start).order_by(Trade.executed_at.desc())
        return list(self.db.scalars(stmt).all())

    def get_trades_by_date(self, target_date: date) -> List[Trade]:
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())
        stmt = select(Trade).where(Trade.executed_at >= start, Trade.executed_at <= end)
        return list(self.db.scalars(stmt).all())

    def get_daily_trade_count(self) -> int:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        stmt = select(func.count(Trade.id)).where(Trade.executed_at >= today_start)
        return self.db.scalar(stmt) or 0


class PositionRepository(BaseRepository[Position]):
    def __init__(self, db: Session):
        super().__init__(Position, db)

    def get_active_positions(self) -> List[Position]:
        stmt = select(Position).where(Position.is_open == True)
        return list(self.db.scalars(stmt).all())

    def get_by_symbol(self, symbol: str) -> Optional[Position]:
        stmt = select(Position).where(Position.symbol == symbol, Position.is_open == True)
        return self.db.scalars(stmt).first()

    def upsert_position(self, symbol: str, exchange: str, product: Any, quantity: int, price: float, is_buy: bool) -> Position:
        pos = self.get_by_symbol(symbol)
        if not pos:
            pos_data = {
                "symbol": symbol,
                "exchange": exchange,
                "product": product,
                "quantity": quantity if is_buy else -quantity,
                "buy_price": price if is_buy else 0.0,
                "sell_price": 0.0 if is_buy else price,
                "is_open": True
            }
            return self.create(pos_data)

        new_qty = pos.quantity + (quantity if is_buy else -quantity)
        if new_qty == 0:
            pos.is_open = False
            pos.quantity = 0
        else:
            pos.quantity = new_qty
            if is_buy:
                pos.buy_price = price
            else:
                pos.sell_price = price

        self.db.commit()
        self.db.refresh(pos)
        return pos


class ReportRepository(BaseRepository[Report]):
    def __init__(self, db: Session):
        super().__init__(Report, db)

    def get_latest_report(self) -> Optional[Report]:
        stmt = select(Report).order_by(Report.report_date.desc())
        return self.db.scalars(stmt).first()


class SettingsRepository(BaseRepository[SystemSettings]):
    def __init__(self, db: Session):
        super().__init__(SystemSettings, db)

    def get_by_key(self, key: str) -> Optional[SystemSettings]:
        stmt = select(SystemSettings).where(SystemSettings.key == key)
        return self.db.scalars(stmt).first()

    def set_value(self, key: str, value: str, description: Optional[str] = None) -> SystemSettings:
        setting = self.get_by_key(key)
        if setting:
            setting.value = value
            if description:
                setting.description = description
            self.db.commit()
            self.db.refresh(setting)
            return setting
        else:
            return self.create({"key": key, "value": value, "description": description})


class SystemLogRepository(BaseRepository[SystemLog]):
    def __init__(self, db: Session):
        super().__init__(SystemLog, db)

    def get_recent_logs(self, limit: int = 100, level: Optional[str] = None) -> List[SystemLog]:
        stmt = select(SystemLog)
        if level:
            stmt = stmt.where(SystemLog.level == level.upper())
        stmt = stmt.order_by(SystemLog.created_at.desc()).limit(limit)
        return list(self.db.scalars(stmt).all())
