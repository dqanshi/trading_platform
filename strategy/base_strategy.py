from abc import ABC, abstractmethod
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from broker.kite_client import KiteClient
from broker.order_manager import OrderManager
from engine.risk_manager import RiskManager
from engine.position_manager import PositionManager


class BaseStrategy(ABC):
    """
    Abstract Base Class defining the contract for all algorithmic trading strategies.
    """

    def __init__(
        self,
        name: str,
        db: Session,
        kite_client: KiteClient,
        order_manager: OrderManager,
        risk_manager: RiskManager,
        position_manager: PositionManager
    ):
        self.name = name
        self.db = db
        self.kite_client = kite_client
        self.order_manager = order_manager
        self.risk_manager = risk_manager
        self.position_manager = position_manager
        self.is_active: bool = False

    @abstractmethod
    def start(self) -> None:
        """Initialize and activate the strategy."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Deactivate the strategy and release resources."""
        pass

    @abstractmethod
    def on_tick(self, ticks: List[Dict[str, Any]]) -> None:
        """Process real-time price tick updates."""
        pass
