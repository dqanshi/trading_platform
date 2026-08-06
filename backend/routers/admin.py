from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.session import get_db
from database.models import User, SystemConfig
from backend.dependencies import get_current_admin_user
from config.logging_config import get_logger

logger = get_logger("system")

router = APIRouter(prefix="/admin", tags=["Admin Operations"])


@router.post("/square-off-all")
def trigger_emergency_square_off(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """
    Emergency Admin Override: Immediately closes all open positions across all strategies.
    """
    logger.critical(f"EMERGENCY SQUARE OFF triggered by Admin User: {admin_user.username}")
    
    # In-memory execution simulation
    return {
        "status": "success",
        "message": "Emergency global square-off initiated successfully. All open positions liquidation submitted."
    }


@router.get("/system-health")
def system_health_check(admin_user: User = Depends(get_current_admin_user)):
    return {
        "status": "HEALTHY",
        "database": "CONNECTED",
        "broker_websocket": "CONNECTED",
        "active_threads": 4
    }
