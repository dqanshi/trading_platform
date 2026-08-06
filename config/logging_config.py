import os
import sys
import logging
from logging.handlers import RotatingFileHandler


def setup_logging():
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    app_file_handler = RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=10485760,
        backupCount=5
    )
    app_file_handler.setFormatter(formatter)
    app_file_handler.setLevel(logging.INFO)

    error_file_handler = RotatingFileHandler(
        os.path.join(log_dir, "errors.log"),
        maxBytes=10485760,
        backupCount=5
    )
    error_file_handler.setFormatter(formatter)
    error_file_handler.setLevel(logging.ERROR)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(app_file_handler)
    root_logger.addHandler(error_file_handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


setup_logging()
