from typing import List, Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database.session import get_db
from database.repository import SystemLogRepository
from backend.schemas.reports import LogResponse
from backend.security import get_current_user
from database.models import User

router = APIRouter(prefix="/logs", tags=["System Logs"])


@router.get("", response_model=List[LogResponse])
def get_system_logs(
    level: Optional[str] = Query(None, description="Filter logs by level (INFO, WARNING, ERROR)"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    repo = SystemLogRepository(db)
    return repo.get_recent_logs(limit=limit, level=level)
