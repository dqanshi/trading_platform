from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.config import settings
from config.logging_config import get_logger
from database.session import init_db
from backend.routers import (
    auth_router, trading_router, settings_router, reports_router, logs_router
)

logger = get_logger("system")

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(trading_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(logs_router, prefix="/api/v1")


@app.on_event("startup")
def on_startup() -> None:
    logger.info("Initializing database tables...")
    init_db()
    logger.info(f"{settings.APP_NAME} backend service initialized successfully.")


@app.get("/health", tags=["System"])
def health_check() -> dict:
    return {
        "status": "online",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=(settings.APP_ENV == "development")
    )
