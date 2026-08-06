import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from config.logging_config import get_logger

logger = get_logger("system")


class ProcessTimeLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware measuring API request duration and logging slow endpoint execution times.
    """

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)

        if process_time > 1.0:
            logger.warning(
                f"Slow Endpoint Detected: {request.method} {request.url.path} took {process_time:.3f}s"
            )
        return response
