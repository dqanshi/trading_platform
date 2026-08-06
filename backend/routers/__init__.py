from backend.routers.auth import router as auth_router
from backend.routers.trading import router as trading_router
from backend.routers.settings import router as settings_router
from backend.routers.reports import router as reports_router
from backend.routers.logs import router as logs_router

__all__ = [
    "auth_router",
    "trading_router",
    "settings_router",
    "reports_router",
    "logs_router"
]
