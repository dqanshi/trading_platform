import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from broker.kite_client import KiteClient
from broker.websocket import KiteWebSocketManager
from broker.order_manager import OrderManager
from engine.risk_manager import RiskManager
from engine.position_manager import PositionManager
from strategy.orb_strategy import ORBStrategy
from strategy.momentum_scanner import HighMomentumScanner
from database.repository import OrderRepository, TradeRepository, PositionRepository
from config.config import settings
from config.logging_config import get_logger

logger = get_logger("system")


class TradingEngine:
    """
    Central Coordinator managing strategy execution, broker connections,
    background schedulers, position monitoring, and overall system state.
    """

    def __init__(self, db: Session, kite_client: KiteClient):
        self.db = db
        self.kite_client = kite_client
        self.ws_manager = KiteWebSocketManager(
            api_key=kite_client.api_key,
            access_token=kite_client.access_token
        )
        self.order_manager = OrderManager(kite_client, db)
        self.risk_manager = RiskManager(db, kite_client)
        self.position_manager = PositionManager(db, self.order_manager)
        
        self.scheduler = BackgroundScheduler()
        self.is_running: bool = False
        self.active_strategy: Optional[ORBStrategy] = None
        self.watchlist: Dict[str, int] = {}
        
        self._setup_websocket_callbacks()
        self._setup_scheduled_tasks()

    def _setup_websocket_callbacks(self) -> None:
        def handle_ticks(ticks: List[Dict[str, Any]]) -> None:
            self.position_manager.on_tick(ticks)
            if self.active_strategy and self.active_strategy.is_active:
                self.active_strategy.on_tick(ticks)

        self.ws_manager.register_tick_callback(handle_ticks)

    def _setup_scheduled_tasks(self) -> None:
        self.scheduler.add_job(
            self.position_manager.check_eod_square_off,
            "interval",
            minutes=1,
            id="eod_square_off_job"
        )
        self.scheduler.add_job(
            self.order_manager.sync_orders,
            "interval",
            seconds=10,
            id="sync_orders_job"
        )

    def set_watchlist(self, watchlist: Dict[str, int]) -> None:
        self.watchlist = watchlist
        tokens = list(watchlist.values())
        if tokens and self.ws_manager.is_connected:
            self.ws_manager.subscribe(tokens)

    def start_algo(self, strategy_name: str = "ORB", watchlist: Optional[Dict[str, int]] = None) -> None:
        if self.is_running:
            logger.warning("Algo Trading Engine is already running")
            return

        if watchlist:
            self.watchlist = watchlist

        if not self.kite_client.is_authenticated():
            raise RuntimeError("Kite Client is not authenticated. Please provide a valid session token.")

        if self.kite_client.access_token:
            self.ws_manager.initialize(self.kite_client.access_token)
            self.ws_manager.connect()

        if self.watchlist:
            tokens = list(self.watchlist.values())
            self.ws_manager.subscribe(tokens)

        if strategy_name.upper() == "ORB":
            self.active_strategy = ORBStrategy(
                db=self.db,
                kite_client=self.kite_client,
                order_manager=self.order_manager,
                risk_manager=self.risk_manager,
                position_manager=self.position_manager,
                watchlist=self.watchlist
            )
            self.active_strategy.start()

        if not self.scheduler.running:
            self.scheduler.start()

        self.is_running = True
        logger.info(f"Algo Engine started successfully with strategy '{strategy_name}'")

    def stop_algo(self) -> None:
        if not self.is_running:
            logger.warning("Algo Trading Engine is not currently running")
            return

        if self.active_strategy:
            self.active_strategy.stop()
            self.active_strategy = None

        self.position_manager.square_off_all_positions(reason="ALGO_STOPPED")

        if self.ws_manager.is_connected:
            self.ws_manager.disconnect()

        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

        self.is_running = False
        logger.info("Algo Engine stopped successfully")

    def get_status(self) -> Dict[str, Any]:
        trade_repo = TradeRepository(self.db)
        position_repo = PositionRepository(self.db)
        
        trades_today = trade_repo.get_todays_trades()
        realized_pnl = sum(t.pnl for t in trades_today)
        
        active_positions = position_repo.get_active_positions()
        unrealized_pnl = sum(p.m2m for p in active_positions)

        return {
            "is_running": self.is_running,
            "websocket_connected": self.ws_manager.is_connected,
            "kite_authenticated": self.kite_client.is_authenticated(),
            "active_strategy": self.active_strategy.name if self.active_strategy else None,
            "total_trades_today": len(trades_today),
            "realized_pnl_today": round(realized_pnl, 2),
            "unrealized_pnl_today": round(unrealized_pnl, 2),
            "open_positions_count": len(active_positions)
        }
