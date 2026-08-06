import os
from datetime import time
from typing import Optional
from pydantic import Field, PostgresDsn, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    APP_NAME: str = "Zerodha Algorithmic Trading Platform"
    APP_ENV: str = "production"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str
    DATABASE_URL: Optional[str] = None

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str) and v:
            return v
        return str(
            PostgresDsn.build(
                scheme="postgresql+psycopg2",
                username=values.get("POSTGRES_USER"),
                password=values.get("POSTGRES_PASSWORD"),
                host=values.get("POSTGRES_SERVER"),
                port=values.get("POSTGRES_PORT"),
                path=f"{values.get('POSTGRES_DB') or ''}",
            )
        )

    KITE_API_KEY: str
    KITE_API_SECRET: str
    KITE_ACCESS_TOKEN: Optional[str] = None

    MAX_DAILY_LOSS: float = Field(default=5000.0, ge=0.0)
    MAX_TRADES_PER_DAY: int = Field(default=20, ge=1)
    MAX_POSITION_SIZE: float = Field(default=50000.0, ge=0.0)
    SL_PERCENTAGE: float = Field(default=1.0, ge=0.1, le=100.0)
    TARGET_PERCENTAGE: float = Field(default=2.0, ge=0.1, le=100.0)
    TRAILING_SL_PERCENTAGE: float = Field(default=0.5, ge=0.0, le=50.0)
    MAX_REPEATED_FAILURES: int = Field(default=3, ge=1)
    
    TRADING_WINDOW_START: str = "09:15"
    TRADING_WINDOW_END: str = "15:15"
    SQUARE_OFF_TIME: str = "15:15"

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./logs"

    def get_parsed_trading_start(self) -> time:
        hour, minute = map(int, self.TRADING_WINDOW_START.split(":"))
        return time(hour, minute)

    def get_parsed_trading_end(self) -> time:
        hour, minute = map(int, self.TRADING_WINDOW_END.split(":"))
        return time(hour, minute)

    def get_parsed_square_off_time(self) -> time:
        hour, minute = map(int, self.SQUARE_OFF_TIME.split(":"))
        return time(hour, minute)


settings = Settings()
