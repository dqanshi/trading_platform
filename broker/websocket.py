import threading
from typing import List, Dict, Any, Callable, Optional
from kiteconnect import KiteTicker
from config.config import settings
from config.logging_config import get_logger

logger = get_logger("system")


class KiteWebSocketManager:
    def __init__(self, api_key: Optional[str] = None, access_token: Optional[str] = None):
        self.api_key = api_key or settings.KITE_API_KEY
        self.access_token = access_token or settings.KITE_ACCESS_TOKEN
        self.kws: Optional[KiteTicker] = None
        self.is_connected: bool = False
        self.subscribed_tokens: List[int] = []
        self.tick_callbacks: List[Callable[[List[Dict[str, Any]]], None]] = []
        self.order_update_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self._thread: Optional[threading.Thread] = None

    def initialize(self, access_token: str) -> None:
        self.access_token = access_token
        self.kws = KiteTicker(api_key=self.api_key, access_token=self.access_token)
        self._bind_callbacks()

    def _bind_callbacks(self) -> None:
        if not self.kws:
            return

        def on_ticks(ws, ticks):
            for cb in self.tick_callbacks:
                try:
                    cb(ticks)
                except Exception as e:
                    logger.error(f"Error in tick callback execution: {str(e)}")

        def on_connect(ws, response):
            self.is_connected = True
            logger.info("WebSocket connection established successfully")
            if self.subscribed_tokens:
                ws.subscribe(self.subscribed_tokens)
                ws.set_mode(ws.MODE_FULL, self.subscribed_tokens)

        def on_close(ws, code, reason):
            self.is_connected = False
            logger.warning(f"WebSocket closed: Code {code} - Reason: {reason}")

        def on_error(ws, code, reason):
            logger.error(f"WebSocket error: Code {code} - Reason: {reason}")

        def on_reconnect(ws, attempt_count):
            logger.info(f"WebSocket reconnecting... Attempt #{attempt_count}")

        def on_noreconnect(ws):
            self.is_connected = False
            logger.error("WebSocket reconnection failed. Exceeded max attempts.")

        def on_order_update(ws, data):
            logger.info(f"Order update received via WebSocket: {data}")
            for cb in self.order_update_callbacks:
                try:
                    cb(data)
                except Exception as e:
                    logger.error(f"Error in order update callback: {str(e)}")

        self.kws.on_ticks = on_ticks
        self.kws.on_connect = on_connect
        self.kws.on_close = on_close
        self.kws.on_error = on_error
        self.kws.on_reconnect = on_reconnect
        self.kws.on_noreconnect = on_noreconnect
        self.kws.on_order_update = on_order_update

    def register_tick_callback(self, callback: Callable[[List[Dict[str, Any]]], None]) -> None:
        if callback not in self.tick_callbacks:
            self.tick_callbacks.append(callback)

    def register_order_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        if callback not in self.order_update_callbacks:
            self.order_update_callbacks.append(callback)

    def connect(self) -> None:
        if not self.kws:
            if not self.access_token:
                raise ValueError("Cannot connect WebSocket: Access Token is missing")
            self.initialize(self.access_token)

        if self.is_connected:
            return

        self._thread = threading.Thread(target=self.kws.connect, kwargs={"threaded": False}, daemon=True)
        self._thread.start()

    def disconnect(self) -> None:
        if self.kws and self.is_connected:
            self.kws.close()
            self.is_connected = False
            logger.info("WebSocket manually disconnected")

    def subscribe(self, tokens: List[int], mode: str = "full") -> None:
        new_tokens = [t for t in tokens if t not in self.subscribed_tokens]
        if new_tokens:
            self.subscribed_tokens.extend(new_tokens)
            if self.kws and self.is_connected:
                self.kws.subscribe(new_tokens)
                mode_attr = getattr(self.kws, f"MODE_{mode.upper()}", self.kws.MODE_FULL)
                self.kws.set_mode(mode_attr, new_tokens)

    def unsubscribe(self, tokens: List[int]) -> None:
        self.subscribed_tokens = [t for t in self.subscribed_tokens if t not in tokens]
        if self.kws and self.is_connected:
            self.kws.unsubscribe(tokens)
