from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from database.session import Base
from utils.constants import OrderStatus, TransactionType, OrderType, ProductType


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class SystemConfig(Base):
    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(100), unique=True, index=True, nullable=False)
    symbol = Column(String(50), nullable=False)
    exchange = Column(String(20), default="NSE")
    transaction_type = Column(String(20), nullable=False)
    order_type = Column(String(20), nullable=False)
    product = Column(String(20), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, default=0.0)
    trigger_price = Column(Float, default=0.0)
    average_price = Column(Float, default=0.0)
    status = Column(String(30), default=OrderStatus.PENDING.value)
    rejection_reason = Column(Text, nullable=True)
    strategy_name = Column(String(100), default="MANUAL")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), unique=True, index=True, nullable=False)
    exchange = Column(String(20), default="NSE")
    product = Column(String(20), nullable=False)
    quantity = Column(Integer, default=0)
    average_price = Column(Float, default=0.0)
    m2m = Column(Float, default=0.0)
    pnl = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(String(100), unique=True, index=True, nullable=False)
    order_id = Column(String(100), nullable=False)
    symbol = Column(String(50), nullable=False)
    transaction_type = Column(String(20), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    pnl = Column(Float, default=0.0)
    strategy_name = Column(String(100), default="MANUAL")
    executed_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), default="INFO")
    module = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
