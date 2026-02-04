from __future__ import annotations

from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, ConfigDict


class Mode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    environment: Literal["paper", "live"]
    kill_switch: bool


class BrokerStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: Literal["connected", "degraded", "down"]
    latency_ms: int | None


class WorkerStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: Literal["running", "stopped", "error"]
    last_heartbeat_at: datetime


class DataStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: Literal["ok", "lagging", "down"]
    lag_seconds: int


class StatusBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    broker: BrokerStatus
    worker: WorkerStatus
    data: DataStatus


class AccountBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    equity: float
    cash: float
    today_pnl: PnlBlock
    active_positions: ActivePositionsBlock


class PnlBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: float
    pct: float


class ActivePositionsBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int
    new_today: int


class SelectedMetricBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    value: float
    unit: str
    window: str


class KpiBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    today_pnl: PnlBlock
    total_pnl: PnlBlock
    active_positions: ActivePositionsBlock
    selected_metric: SelectedMetricBlock


class EquityPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    t: datetime
    equity: float


class PerformanceSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    return_pct: float
    max_drawdown_pct: float


class PerformanceBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    range: str
    equity_curve: List[EquityPoint]
    summary: PerformanceSummary


class BotRunBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    started_at: datetime
    ended_at: datetime | None
    result: Literal["success", "failed", "partial"]
    orders_created: int
    orders_failed: int


class BotBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: Literal["running", "stopped", "error"]
    last_run: BotRunBlock
    next_run_at: datetime


class ActiveStrategyBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy_id: str
    name: str
    state: Literal["running", "paused", "idle", "error"]
    positions_count: int
    managed_value: float
    pnl_today: PnlBlock


class RecentTradeBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fill_id: str
    filled_at: datetime
    symbol: str
    side: Literal["buy", "sell"]
    qty: float
    price: float
    strategy_id: str
    strategy_name: str


class AlertLink(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: str
    tab: str | None = None


class AlertBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alert_id: str
    severity: Literal["info", "warning", "critical"]
    type: str
    title: str
    message: str
    occurred_at: datetime
    link: AlertLink


class DashboardResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Mode
    status: StatusBlock
    account: AccountBlock
    kpi: KpiBlock
    performance: PerformanceBlock
    bot: BotBlock
    active_strategies: List[ActiveStrategyBlock]
    recent_trades: List[RecentTradeBlock]
    alerts: List[AlertBlock]
