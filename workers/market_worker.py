import time
from broker.websocket import KiteWebSocketManager
from config.config import settings
from config.logging_config import get_logger

logger = get_logger("system")


def start_market_worker(access_token: str, tokens: list):
    """
    Standalone market data stream worker process.
    """
    logger.info("Starting standalone Market Data Streaming Worker...")
    ws = KiteWebSocketManager(api_key=settings.KITE_API_KEY, access_token=access_token)

    def on_ticks(ticks):
        logger.debug(f"Received {len(ticks)} ticks in worker process.")

    ws.register_tick_callback(on_ticks)
    ws.initialize(access_token)
    ws.connect()

    if tokens:
        ws.subscribe(tokens)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        ws.disconnect()
        logger.info("Market worker shut down.")


if __name__ == "__main__":
    if settings.KITE_ACCESS_TOKEN:
        start_market_worker(settings.KITE_ACCESS_TOKEN, [738561, 2953217])
    else:
        logger.error("No KITE_ACCESS_TOKEN found in environment.")
