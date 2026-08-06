from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database.session import get_db
from database.repository import UserRepository
from backend.security import create_access_token, verify_password, get_password_hash, get_current_user
from backend.schemas.auth import Token, UserResponse, UserLogin
from database.models import User
from config.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    user_repo = UserRepository(db)
    user = user_repo.get_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)) -> Any:
    return current_user


@router.post("/setup-initial-admin", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def setup_initial_admin(
    user_data: UserLogin,
    db: Session = Depends(get_db)
) -> Any:
    user_repo = UserRepository(db)
    existing_user = user_repo.get_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )
    
    hashed_pwd = get_password_hash(user_data.password)
    new_user = user_repo.create({
        "username": user_data.username,
        "email": f"{user_data.username}@admin.local",
        "hashed_password": hashed_pwd,
        "is_active": True,
        "is_superuser": True
    })
    return new_user
