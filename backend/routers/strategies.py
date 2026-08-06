from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database.session import get_db
from database.models import Order, User
from backend.schemas.order import OrderCreateRequest, OrderResponse, OrderCancelRequest
from backend.dependencies import get_current_active_user
from broker.order_manager import OrderManager
from broker.kite_client import KiteClient
from config.config import settings
from utils.validators import DataValidator

router = APIRouter(prefix="/orders", tags=["Orders"])

# Single global instance of OrderManager for API execution
_kite_client = KiteClient()
_order_manager = OrderManager(_kite_client)


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def place_order(
    request: OrderCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    valid, msg = DataValidator.validate_order_params(
        request.symbol, request.quantity, request.price,
        request.order_type.value, request.transaction_type.value, request.product.value
    )
    if not valid:
        raise HTTPException(status_code=400, detail=msg)

    try:
        _order_manager.db = db
        order = _order_manager.execute_order(
            symbol=request.symbol,
            exchange=request.exchange,
            transaction_type=request.transaction_type,
            order_type=request.order_type,
            product=request.product,
            quantity=request.quantity,
            price=request.price or 0.0,
            trigger_price=request.trigger_price or 0.0,
            strategy_name=request.strategy_name or "MANUAL"
        )
        return order
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order placement failed: {str(e)}")


@router.get("/", response_model=List[OrderResponse])
def list_orders(
    symbol: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(Order)
    if symbol:
        query = query.filter(Order.symbol == symbol.upper())
    if status_filter:
        query = query.filter(Order.status == status_filter.upper())

    return query.order_by(Order.created_at.desc()).limit(limit).all()


@router.post("/cancel")
def cancel_order(
    request: OrderCancelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    _order_manager.db = db
    success = _order_manager.cancel_order(request.order_id)
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to cancel order ID {request.order_id}")
    return {"status": "success", "message": f"Order {request.order_id} cancellation submitted."}
