from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class SettingUpdate(BaseModel):
    key: str
    value: str
    description: Optional[str] = None


class SettingResponse(BaseModel):
    id: int
    key: str
    value: str
    description: Optional[str] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
