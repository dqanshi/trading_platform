import time
import threading
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from database.session import SessionLocal
from broker.kite_client import KiteClient
from broker.websocket import KiteWebSocketManager
from broker.order_manager import OrderManager
from engine.risk_manager import RiskManager
from engine.position_manager import PositionManager
from engine.portfolio_manager import PortfolioManager
from config.logging_config import get_logger

logger = get_logger("engine")


class TradingEngine:
    """
    Central Trading Engine coordinating WebSocket feed, Risk Checks, Strategies, and Order Routing.
    """

    def __init__(self):
        self.is_running = False
        self.kite_client = KiteClient()
        self.ws_manager = None
        self._thread = None

    def start(self):
        if self.is_running:
            logger.warning("Trading Engine is already running.")
            return

        self.is_running = True
        logger.info("Initializing QuantTerminal Trading Engine...")

        db = SessionLocal()
        try:
            self.risk_manager = RiskManager(db)
            self.position_manager = PositionManager(db)
            self.order_manager = OrderManager(self.kite_client, db)
            self.portfolio_manager = PortfolioManager(db)

            if self.kite_client.access_token:
                self.ws_manager = KiteWebSocketManager(
                    api_key=self.kite_client.api_key,
                    access_token=self.kite_client.access_token
                )
                self.ws_manager.register_tick_callback(self._handle_ticks)
                self.ws_manager.initialize()
                self.ws_manager.connect()

            logger.info("Trading Engine started successfully.")
        finally:
            db.close()

    def stop(self):
        self.is_running = False
        if self.ws_manager:
            self.ws_manager.disconnect()
        logger.info("Trading Engine stopped.")

    def _handle_ticks(self, ticks: List[Dict[str, Any]]):
        if not ticks:
            return

        tick_map = {tick.get("tradingsymbol", ""): tick.get("last_price", 0.0) for tick in ticks if tick.get("tradingsymbol")}

        db = SessionLocal()
        try:
            pos_mgr = PositionManager(db)
            pos_mgr.update_positions_m2m(tick_map)
        except Exception as e:
            logger.error(f"Error handling market ticks in engine: {str(e)}")
        finally:
            db.close()


trading_engine = TradingEngine()
