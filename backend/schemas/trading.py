from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from database.models import TransactionType, OrderType, ProductType, OrderStatus


class OrderCreate(BaseModel):
    symbol: str
    exchange: str = "NSE"
    transaction_type: TransactionType
    order_type: OrderType
    product: ProductType
    quantity: int
    price: float = 0.0
    trigger_price: float = 0.0
    strategy_name: Optional[str] = None


class OrderResponse(BaseModel):
    id: int
    order_id: str
    exchange_order_id: Optional[str] = None
    symbol: str
    exchange: str
    transaction_type: TransactionType
    order_type: OrderType
    product: ProductType
    quantity: int
    filled_quantity: int
    price: float
    trigger_price: float
    status: OrderStatus
    status_message: Optional[str] = None
    strategy_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TradeResponse(BaseModel):
    id: int
    trade_id: str
    order_id: int
    symbol: str
    exchange: str
    transaction_type: TransactionType
    quantity: int
    price: float
    pnl: float
    strategy_name: Optional[str] = None
    executed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PositionResponse(BaseModel):
    id: int
    symbol: str
    exchange: str
    product: ProductType
    quantity: int
    buy_price: float
    sell_price: float
    m2m: float
    pnl: float
    is_open: bool
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlgoStatusResponse(BaseModel):
    is_running: bool
    websocket_connected: bool
    kite_authenticated: bool
    active_strategy: Optional[str] = None
    total_trades_today: int
    realized_pnl_today: float
    unrealized_pnl_today: float
    open_positions_count: int


class AlgoControlRequest(BaseModel):
    strategy_name: Optional[str] = "ORB"
