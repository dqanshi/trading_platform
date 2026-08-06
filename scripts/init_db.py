import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.session import init_db, SessionLocal
from database.repository import UserRepository, SettingsRepository
from backend.security import get_password_hash
from config.logging_config import get_logger

logger = get_logger("system")


def seed_database():
    logger.info("Starting database initialization and seeding...")
    init_db()

    db = SessionLocal()
    try:
        user_repo = UserRepository(db)
        admin_user = user_repo.get_by_username("admin")
        if not admin_user:
            user_repo.create({
                "username": "admin",
                "email": "admin@quantterminal.local",
                "hashed_password": get_password_hash("admin123"),
                "is_active": True,
                "is_superuser": True
            })
            logger.info("Created default admin user (username: 'admin', password: 'admin123')")

        settings_repo = SettingsRepository(db)
        default_settings = [
            ("MAX_DAILY_LOSS", "5000", "Maximum allowed loss in INR per day"),
            ("MAX_DRAWDOWN_PCT", "5.0", "Maximum portfolio drawdown percentage"),
            ("MAX_ORDER_VALUE", "100000", "Maximum value per order in INR"),
            ("EOD_SQUARE_OFF_TIME", "15:15", "Mandatory intraday position square-off time")
        ]

        for key, val, desc in default_settings:
            settings_repo.set_value(key, val, desc)

        logger.info("Database seeding completed successfully.")
    except Exception as e:
        logger.error(f"Error during database seeding: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
