from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class BacktestRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    my_strategy_id: str
    start_date: str
    end_date: str
    benchmark_symbol: Optional[str] = "SPY"
    initial_cash: float = Field(default=100000, gt=0)
    slippage_bps: float = Field(default=0, ge=0)
    fee_bps: float = Field(default=0, ge=0)


class BacktestRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: Optional[str] = None
    my_strategy_id: str
    metrics: Dict[str, float]
    equity_curve: List[Dict[str, float]]
    trade_stats: Dict[str, float]
    benchmark: Optional[Dict[str, object]] = None
