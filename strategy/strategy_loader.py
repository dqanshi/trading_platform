from typing import Dict, Type, Any
from sqlalchemy.orm import Session
from strategy.base_strategy import BaseStrategy
from strategy.orb_strategy import ORBStrategy
from strategy.breakout_strategy import BreakoutStrategy
from strategy.mean_reversion import MeanReversionStrategy
from broker.kite_client import KiteClient
from broker.order_manager import OrderManager
from engine.risk_manager import RiskManager
from engine.position_manager import PositionManager


class StrategyLoader:
    """
    Dynamic strategy registry factory for instantiating trading algorithms by name.
    """

    _REGISTRY: Dict[str, Type[BaseStrategy]] = {
        "ORB": ORBStrategy,
        "BREAKOUT": BreakoutStrategy,
        "MEAN_REVERSION": MeanReversionStrategy
    }

    @classmethod
    def register_strategy(cls, name: str, strategy_cls: Type[BaseStrategy]) -> None:
        cls._REGISTRY[name.upper()] = strategy_cls

    @classmethod
    def load_strategy(
        cls,
        name: str,
        db: Session,
        kite_client: KiteClient,
        order_manager: OrderManager,
        risk_manager: RiskManager,
        position_manager: PositionManager,
        watchlist: Dict[str, int],
        **kwargs
    ) -> BaseStrategy:
        strategy_key = name.upper()
        if strategy_key not in cls._REGISTRY:
            raise ValueError(f"Strategy '{name}' is not registered. Available: {list(cls._REGISTRY.keys())}")

        strategy_cls = cls._REGISTRY[strategy_key]
        return strategy_cls(
            db=db,
            kite_client=kite_client,
            order_manager=order_manager,
            risk_manager=risk_manager,
            position_manager=position_manager,
            watchlist=watchlist,
            **kwargs
        )
