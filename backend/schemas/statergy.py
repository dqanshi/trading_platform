from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any


class StrategyConfigRequest(BaseModel):
    strategy_name: str = Field(..., example="ORB")
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        example={"watchlist": ["RELIANCE", "INFY"], "quantity": 10, "orb_window_minutes": 15}
    )


class StrategyStatusResponse(BaseModel):
    strategy_name: str
    is_active: bool
    watchlist: List[str]
    parameters: Dict[str, Any]


class StrategyControlRequest(BaseModel):
    strategy_name: str = Field(..., example="ORB")
    action: str = Field(..., example="START", description="START or STOP")
