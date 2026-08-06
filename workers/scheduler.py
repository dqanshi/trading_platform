from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
from config.logging_config import get_logger

logger = get_logger("system")

scheduler = BlockingScheduler()


@scheduler.scheduled_job('cron', day_of_week='mon-fri', hour=15, minute=15)
def scheduled_eod_squareoff():
    logger.info("CRON: Triggering EOD Square-Off Job for all open positions.")


@scheduler.scheduled_job('cron', day_of_week='mon-fri', hour=18, minute=0)
def scheduled_daily_report():
    logger.info("CRON: Generating Daily Performance and Trade Reports.")


if __name__ == "__main__":
    logger.info("Starting Background Cron Scheduler Worker...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Cron Scheduler stopped.")
