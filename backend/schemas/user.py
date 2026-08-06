from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, example="trader_john")
    email: EmailStr = Field(..., example="john@quantterminal.com")


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, example="SecurePassword123!")
    is_superuser: bool = Field(default=False)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime

    class Config:
        from_attributes = True
