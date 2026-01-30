from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Literal, List

from pydantic import BaseModel, ConfigDict


class StrategyPnl(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: float
    pct: float


class StrategyItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy_id: str
    name: str
    state: Literal["running", "paused", "idle", "error"]
    description: str
    positions_count: int
    pnl_today: StrategyPnl
    updated_at: datetime


class StrategyListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: List[StrategyItem]


class StrategyDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy_id: str
    name: str
    state: Literal["running", "paused", "idle", "error"]
    description: str
    params: Dict[str, Any]
    risk_limits: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class StrategyStateUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: Literal["running", "paused", "idle"]


class StrategyStateUpdateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy_id: str
    state: Literal["running", "paused", "idle"]
