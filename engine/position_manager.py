from typing import Dict, Any, List
from sqlalchemy.orm import Session
from database.models import Position
from engine.pnl_calculator import PnLCalculator
from config.logging_config import get_logger

logger = get_logger("system")


class PositionManager:
    """
    Monitors live positions and updates M2M valuations based on incoming market tick stream.
    """

    def __init__(self, db: Session):
        self.db = db

    def update_positions_m2m(self, tick_map: Dict[str, float]) -> List[Position]:
        open_positions = self.db.query(Position).filter(Position.quantity != 0).all()
        updated_positions = []

        for pos in open_positions:
            if pos.symbol in tick_map:
                current_price = tick_map[pos.symbol]
                pos.m2m = PnLCalculator.compute_position_m2m(pos, current_price)
                updated_positions.append(pos)

        if updated_positions:
            self.db.commit()

        return open_positions

    def get_all_positions() -> List[Position]:
        return self.db.query(Position).all()
