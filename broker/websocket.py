import threading
from typing import Callable, List, Optional, Dict, Any
from config.logging_config import get_logger

logger = get_logger("websocket")


class KiteWebSocketManager:
    """
    Manages WebSocket streaming connections via KiteTicker for receiving real-time tick data.
    """

    def __init__(self, api_key: str, access_token: str):
        self.api_key = api_key
        self.access_token = access_token
        self.ticker = None
        self.subscribed_tokens: List[int] = []
        self.tick_callbacks: List[Callable[[List[Dict[str, Any]]], None]] = []

    def initialize(self, access_token: Optional[str] = None):
        if access_token:
            self.access_token = access_token

        try:
            from kiteconnect import KiteTicker
            self.ticker = KiteTicker(self.api_key, self.access_token)
            self._bind_events()
        except ImportError:
            logger.warning("KiteTicker not available. WebSocket streaming in mock mode.")
            self.ticker = None

    def _bind_events(self):
        if not self.ticker:
            return

        def on_ticks(ws, ticks):
            for callback in self.tick_callbacks:
                try:
                    callback(ticks)
                except Exception as e:
                    logger.error(f"Error executing tick callback: {str(e)}")

        def on_connect(ws, response):
            logger.info("Kite WebSocket connected successfully.")
            if self.subscribed_tokens:
                ws.subscribe(self.subscribed_tokens)
                ws.set_mode(ws.MODE_FULL, self.subscribed_tokens)

        def on_close(ws, code, reason):
            logger.warning(f"Kite WebSocket disconnected: {code} - {reason}")

        def on_error(ws, code, reason):
            logger.error(f"Kite WebSocket error: {code} - {reason}")

        self.ticker.on_ticks = on_ticks
        self.ticker.on_connect = on_connect
        self.ticker.on_close = on_close
        self.ticker.on_error = on_error

    def register_tick_callback(self, callback: Callable[[List[Dict[str, Any]]], None]):
        self.tick_callbacks.append(callback)

    def subscribe(self, tokens: List[int]):
        self.subscribed_tokens.extend(tokens)
        self.subscribed_tokens = list(set(self.subscribed_tokens))
        if self.ticker and self.ticker.is_connected():
            self.ticker.subscribe(tokens)
            self.ticker.set_mode(self.ticker.MODE_FULL, tokens)

    def connect(self):
        if self.ticker:
            t = threading.Thread(target=self.ticker.connect, kwargs={"threaded": True})
            t.daemon = True
            t.start()
            logger.info("WebSocket connection thread started.")

    def disconnect(self):
        if self.ticker and self.ticker.is_connected():
            self.ticker.close()
