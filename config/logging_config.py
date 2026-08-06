import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from config.config import settings


def setup_logging() -> None:
    log_dir = settings.LOG_DIR
    os.makedirs(log_dir, exist_ok=True)

    log_format = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] [%(filename)s:%(lineno)d] - %(message)s"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL.upper())
    root_logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    console_handler.setLevel(settings.LOG_LEVEL.upper())
    root_logger.addHandler(console_handler)

    log_files = {
        "system": os.path.join(log_dir, "system.log"),
        "api": os.path.join(log_dir, "api.log"),
        "orders": os.path.join(log_dir, "orders.log"),
        "signals": os.path.join(log_dir, "signals.log"),
        "errors": os.path.join(log_dir, "errors.log"),
        "strategy": os.path.join(log_dir, "strategy.log"),
    }

    handlers = {}
    for log_name, file_path in log_files.items():
        file_handler = RotatingFileHandler(
            filename=file_path,
            maxBytes=10 * 1024 * 1024,
            backupCount=10,
            encoding="utf-8"
        )
        file_handler.setFormatter(log_format)
        handlers[log_name] = file_handler

    root_logger.addHandler(handlers["system"])

    error_handler = handlers["errors"]
    error_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_handler)

    for logger_name in ["api", "orders", "signals", "strategy"]:
        dedicated_logger = logging.getLogger(logger_name)
        dedicated_logger.setLevel(settings.LOG_LEVEL.upper())
        dedicated_logger.addHandler(handlers[logger_name])
        dedicated_logger.propagate = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


setup_logging()
