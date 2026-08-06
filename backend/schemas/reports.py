from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ReportResponse(BaseModel):
    id: int
    report_date: datetime
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    max_drawdown: float
    csv_file_path: Optional[str] = None
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LogResponse(BaseModel):
    id: int
    level: str
    module: str
    message: str
    metadata_json: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
