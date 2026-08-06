import os
import csv
from datetime import datetime, date
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from database.repository import TradeRepository, ReportRepository
from database.models import Report
from config.config import settings
from config.logging_config import get_logger

logger = get_logger("system")


class ReportGenerator:
    """
    Generates daily operational reports, calculates performance metrics
    (PnL, win rate, drawdown), and exports summary CSV records.
    """

    def __init__(self, db: Session):
        self.db = db
        self.trade_repo = TradeRepository(db)
        self.report_repo = ReportRepository(db)

    def generate_daily_report(self, report_date: Optional[date] = None) -> Report:
        target_date = report_date or datetime.utcnow().date()
        trades = self.trade_repo.get_trades_by_date(target_date)

        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t.pnl > 0)
        losing_trades = sum(1 for t in trades if t.pnl < 0)
        win_rate = (winning_trades / total_trades * 100.0) if total_trades > 0 else 0.0
        total_pnl = sum(t.pnl for t in trades)

        cumulative_pnl = 0.0
        peak_pnl = 0.0
        max_drawdown = 0.0

        for t in sorted(trades, key=lambda x: x.executed_at):
            cumulative_pnl += t.pnl
            if cumulative_pnl > peak_pnl:
                peak_pnl = cumulative_pnl
            drawdown = peak_pnl - cumulative_pnl
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        csv_path = self._export_trades_to_csv(target_date, trades)

        report_data = {
            "report_date": datetime.combine(target_date, datetime.min.time()),
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": round(win_rate, 2),
            "total_pnl": round(total_pnl, 2),
            "max_drawdown": round(max_drawdown, 2),
            "csv_file_path": csv_path,
            "generated_at": datetime.utcnow()
        }

        report = self.report_repo.create(report_data)
        logger.info(f"Daily report generated for {target_date}. PnL: {total_pnl:.2f} | Win Rate: {win_rate:.2f}%")
        return report

    def _export_trades_to_csv(self, target_date: date, trades: list) -> str:
        reports_dir = os.path.join(os.getcwd(), "reports_data")
        os.makedirs(reports_dir, exist_ok=True)
        file_name = f"trade_report_{target_date.strftime('%Y_%m_%d')}.csv"
        file_path = os.path.join(reports_dir, file_name)

        fieldnames = [
            "trade_id", "symbol", "exchange", "transaction_type",
            "quantity", "price", "pnl", "strategy_name", "executed_at"
        ]

        with open(file_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for t in trades:
                writer.writerow({
                    "trade_id": t.trade_id,
                    "symbol": t.symbol,
                    "exchange": t.exchange,
                    "transaction_type": t.transaction_type.value,
                    "quantity": t.quantity,
                    "price": t.price,
                    "pnl": t.pnl,
                    "strategy_name": t.strategy_name or "N/A",
                    "executed_at": t.executed_at.strftime("%Y-%m-%d %H:%M:%S")
                })

        return file_path
