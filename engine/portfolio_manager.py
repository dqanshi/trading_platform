from typing import Dict, List, Any
from sqlalchemy.orm import Session
from database.models import Position, Trade, OrderStatus
from engine.pnl_calculator import PnLCalculator
from config.logging_config import get_logger

logger = get_logger("system")


class PortfolioManager:
    """
    Manages total portfolio capital allocation, margin utilization, cash balance, and exposure metrics.
    """

    def __init__(self, db: Session, total_capital: float = 1000000.0):
        self.db = db
        self.total_capital = total_capital

    def get_portfolio_summary(self, current_prices: Dict[str, float]) -> Dict[str, Any]:
        open_positions = self.db.query(Position).filter(Position.quantity != 0).all()
        completed_trades = self.db.query(Trade).all()

        total_margin_used = 0.0
        total_unrealized_pnl = 0.0

        for pos in open_positions:
            ltp = current_prices.get(pos.symbol, pos.average_price)
            m2m = PnLCalculator.compute_position_m2m(pos, ltp)
            total_unrealized_pnl += m2m
            total_margin_used += abs(pos.quantity) * pos.average_price

        total_realized_pnl = PnLCalculator.calculate_total_realized_pnl(completed_trades)
        net_pnl = total_realized_pnl + total_unrealized_pnl
        current_equity = self.total_capital + net_pnl
        available_margin = max(0.0, current_equity - total_margin_used)

        return {
            "total_capital": self.total_capital,
            "current_equity": round(current_equity, 2),
            "margin_used": round(total_margin_used, 2),
            "available_margin": round(available_margin, 2),
            "realized_pnl": round(total_realized_pnl, 2),
            "unrealized_pnl": round(total_unrealized_pnl, 2),
            "net_pnl": round(net_pnl, 2),
            "open_positions_count": len(open_positions),
            "total_trades_count": len(completed_trades)
        }

    def get_position_allocations(self) -> List[Dict[str, Any]]:
        open_positions = self.db.query(Position).filter(Position.quantity != 0).all()
        total_exposure = sum(abs(p.quantity) * p.average_price for p in open_positions)

        allocations = []
        for pos in open_positions:
            exposure = abs(pos.quantity) * pos.average_price
            weight = (exposure / total_exposure * 100) if total_exposure > 0 else 0.0
            allocations.append({
                "symbol": pos.symbol,
                "quantity": pos.quantity,
                "exposure": round(exposure, 2),
                "weight_percentage": round(weight, 2)
            })

        return allocations
