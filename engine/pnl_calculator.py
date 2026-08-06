from typing import List, Dict, Any
from database.models import Position, Trade


class PnLCalculator:
    """
    Calculates Realized, Unrealized (M2M), and Net PnL metrics across trades and open positions.
    """

    @staticmethod
    def compute_position_m2m(position: Position, current_price: float) -> float:
        if position.quantity == 0 or current_price <= 0:
            return 0.0

        if position.quantity > 0:
            return (current_price - position.average_price) * position.quantity
        else:
            return (position.average_price - current_price) * abs(position.quantity)

    @staticmethod
    def calculate_total_realized_pnl(trades: List[Trade]) -> float:
        return sum(t.pnl for t in trades)

    @staticmethod
    def calculate_portfolio_metrics(positions: List[Position], trades: List[Trade]) -> Dict[str, float]:
        realized = sum(t.pnl for t in trades)
        unrealized = sum(p.m2m for p in positions)
        net_pnl = realized + unrealized
        
        return {
            "realized_pnl": round(realized, 2),
            "unrealized_pnl": round(unrealized, 2),
            "net_pnl": round(net_pnl, 2)
        }
