from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.session import get_db
from database.repository import SettingsRepository
from backend.schemas.settings import SettingResponse, SettingUpdate
from backend.security import get_current_user
from database.models import User

router = APIRouter(prefix="/settings", tags=["System Settings"])


@router.get("", response_model=List[SettingResponse])
def get_all_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    repo = SettingsRepository(db)
    return repo.get_all()


@router.get("/{key}", response_model=SettingResponse)
def get_setting_by_key(
    key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    repo = SettingsRepository(db)
    setting = repo.get_by_key(key)
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting key '{key}' not found"
        )
    return setting


@router.post("", response_model=SettingResponse)
def update_setting(
    setting_data: SettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    repo = SettingsRepository(db)
    setting = repo.set_value(
        key=setting_data.key,
        value=setting_data.value,
        description=setting_data.description
    )
    return setting
