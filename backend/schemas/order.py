from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from utils.constants import TransactionType, OrderType, ProductType, OrderStatus


class OrderCreateRequest(BaseModel):
    symbol: str = Field(..., example="RELIANCE")
    exchange: str = Field(default="NSE", example="NSE")
    transaction_type: TransactionType = Field(..., example=TransactionType.BUY)
    order_type: OrderType = Field(default=OrderType.MARKET, example=OrderType.MARKET)
    product: ProductType = Field(default=ProductType.MIS, example=ProductType.MIS)
    quantity: int = Field(..., gt=0, example=10)
    price: Optional[float] = Field(default=0.0, ge=0.0, example=2500.50)
    trigger_price: Optional[float] = Field(default=0.0, ge=0.0, example=0.0)
    strategy_name: Optional[str] = Field(default="MANUAL", example="ORB_5MIN")


class OrderResponse(BaseModel):
    id: int
    order_id: str
    symbol: str
    exchange: str
    transaction_type: str
    order_type: str
    product: str
    quantity: int
    price: float
    trigger_price: float
    average_price: float
    status: OrderStatus
    rejection_reason: Optional[str] = None
    strategy_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderCancelRequest(BaseModel):
    order_id: str = Field(..., example="240806000123456")
