from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.session import get_db
from database.repository import OrderRepository, TradeRepository, PositionRepository
from backend.schemas.trading import (
    OrderResponse, TradeResponse, PositionResponse, AlgoStatusResponse, AlgoControlRequest
)
from backend.security import get_current_user
from database.models import User
from broker.kite_client import KiteClient
from engine.trading_engine import TradingEngine

router = APIRouter(prefix="/trading", tags=["Trading Operations"])

global_kite_client = KiteClient()
global_trading_engine: Optional[TradingEngine] = None


def get_engine(db: Session = Depends(get_db)) -> TradingEngine:
    global global_trading_engine
    if global_trading_engine is None:
        global_trading_engine = TradingEngine(db=db, kite_client=global_kite_client)
    else:
        global_trading_engine.db = db
        global_trading_engine.order_manager.db = db
        global_trading_engine.position_manager.db = db
        global_trading_engine.risk_manager.db = db
    return global_trading_engine


@router.post("/start", response_model=AlgoStatusResponse)
def start_algo(
    request: AlgoControlRequest,
    engine: TradingEngine = Depends(get_engine),
    current_user: User = Depends(get_current_user)
) -> Any:
    try:
        sample_watchlist = {
            "RELIANCE": 738561,
            "TCS": 2953217,
            "INFY": 408065,
            "HDFCBANK": 341249
        }
        engine.start_algo(
            strategy_name=request.strategy_name or "ORB",
            watchlist=sample_watchlist
        )
        return engine.get_status()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start trading engine: {str(e)}"
        )


@router.post("/stop", response_model=AlgoStatusResponse)
def stop_algo(
    engine: TradingEngine = Depends(get_engine),
    current_user: User = Depends(get_current_user)
) -> Any:
    try:
        engine.stop_algo()
        return engine.get_status()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop trading engine: {str(e)}"
        )


@router.get("/status", response_model=AlgoStatusResponse)
def get_status(
    engine: TradingEngine = Depends(get_engine),
    current_user: User = Depends(get_current_user)
) -> Any:
    return engine.get_status()


@router.get("/positions", response_model=List[PositionResponse])
def get_active_positions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    pos_repo = PositionRepository(db)
    return pos_repo.get_active_positions()


@router.get("/orders", response_model=List[OrderResponse])
def get_todays_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    order_repo = OrderRepository(db)
    return order_repo.get_todays_orders()


@router.get("/trades", response_model=List[TradeResponse])
def get_todays_trades(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    trade_repo = TradeRepository(db)
    return trade_repo.get_todays_trades()


@router.post("/square-off/{symbol}")
def square_off_position(
    symbol: str,
    engine: TradingEngine = Depends(get_engine),
    current_user: User = Depends(get_current_user)
) -> Any:
    try:
        engine.position_manager.square_off_position(symbol, reason="MANUAL_REST_TRIGGER")
        return {"status": "success", "message": f"Square off initiated for {symbol}"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Square off failed for {symbol}: {str(e)}"
        )
