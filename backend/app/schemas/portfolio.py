from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


EnvLiteral = Literal["paper", "live"]
RangeLiteral = Literal["1W", "1M", "3M", "1Y", "ALL"]


class PnlBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: float
    pct: float


class ModeBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    environment: EnvLiteral
    kill_switch: bool


class BrokerStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: Literal["up", "down", "degraded"]
    latency_ms: int


class WorkerStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: Literal["running", "stopped", "error", "queued"]
    last_heartbeat_at: str


class StatusBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    broker: BrokerStatus
    worker: WorkerStatus


class OpenPositionsBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int
    long: int
    short: int


class AccountBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    equity: float
    cash: float
    buying_power: float
    today_pnl: PnlBlock
    open_positions: OpenPositionsBlock


class ExposureBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    net_pct: float
    gross_pct: float
    cash_pct: float
    top5_concentration_pct: float


class PortfolioSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    env: EnvLiteral
    as_of: str
    mode: ModeBlock
    status: StatusBlock
    account: AccountBlock
    exposure: ExposureBlock


class PortfolioOverviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    env: EnvLiteral
    as_of: str
    summary: PortfolioSummaryResponse
    allocation: "PortfolioAllocationResponse"


class EquityPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    t: str
    equity: float


class BenchmarkPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    t: str
    price: float


class PortfolioPerformanceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    env: EnvLiteral
    range: RangeLiteral
    benchmark: str
    as_of: str
    equity_curve: List[EquityPoint]
    benchmark_curve: List[BenchmarkPoint]


class DrawdownPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    t: str
    drawdown_pct: float


class DrawdownSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_drawdown_pct: float
    max_drawdown_pct: float


class PortfolioDrawdownResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    env: EnvLiteral
    range: RangeLiteral
    drawdown_curve: List[DrawdownPoint]
    summary: DrawdownSummary


class PortfolioKpi(BaseModel):
    model_config = ConfigDict(extra="forbid")

    period_return_pct: float
    cagr_pct: float
    volatility_pct: float
    sharpe: float
    max_drawdown_pct: float
    win_rate_pct: float


class PortfolioKpiResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    env: EnvLiteral
    range: RangeLiteral
    kpi: PortfolioKpi


class PositionStrategyRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_strategy_id: str
    name: str


class PositionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    qty: float
    side: Literal["long", "short"]
    avg_entry_price: float
    current_price: float
    market_value: float
    unrealized_pnl: PnlBlock
    strategy: PositionStrategyRef


class PortfolioPositionsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    env: EnvLiteral
    items: List[PositionItem]


class SectorAllocation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sector: str
    value: float
    pct: float
    pnl_value: float


class StrategyAllocation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_strategy_id: str
    name: str
    value: float
    pct: float
    pnl_value: float


class PortfolioAllocationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    env: EnvLiteral
    by_sector: List[SectorAllocation]
    by_strategy: List[StrategyAllocation]
    exposure: ExposureBlock


class AttributionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    label: str
    exposure_pct: float
    unrealized_pnl_value: float
    period_contribution_pct: float


class PortfolioAttributionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    env: EnvLiteral
    range: Optional[RangeLiteral] = None
    by: Literal["strategy", "sector"]
    items: List[AttributionItem]


class RiskLimits(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_weight_per_asset: float
    cash_buffer: float
    max_turnover_pct: Optional[float] = None


class UserStrategySummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_strategy_id: str
    name: str
    public_strategy_id: str
    state: Literal["running", "paused", "stopped", "idle", "error"]
    positions_count: int
    today_pnl: PnlBlock
    last_run_at: str
    params: Dict[str, Any]
    risk_limits: RiskLimits


class UserStrategiesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    env: EnvLiteral
    items: List[UserStrategySummary]


class PublicStrategyBrief(BaseModel):
    model_config = ConfigDict(extra="forbid")

    public_strategy_id: str
    name: str
    one_liner: str
    param_schema: Dict[str, Any]


class StrategyRunSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    started_at: str
    status: Literal["success", "failed", "running", "queued"]
    orders_created: int


class UserStrategyDetailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    env: EnvLiteral
    user_strategy_id: str
    name: str
    state: Literal["running", "paused", "stopped", "idle", "error"]
    public_strategy: PublicStrategyBrief
    params: Dict[str, Any]
    risk_limits: RiskLimits
    recent_runs: List[StrategyRunSummary]


class UpdateUserStrategyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    risk_limits: Optional[RiskLimits] = None


class UpdateUserStrategyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    user_strategy_id: str
    updated_at: str


class StrategyStateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["start", "pause", "stop"]


class StrategyStateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    user_strategy_id: str
    state: Literal["running", "paused", "stopped"]


class RebalanceOverrides(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cash_buffer: Optional[float] = None


class PortfolioRebalanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["dry_run", "execute"]
    target_source: Literal["combined", "strategy"]
    strategy_ids: Optional[List[str]] = None
    target_weights: Optional[Dict[str, float]] = None
    target_cash_pct: Optional[float] = Field(default=None, ge=0, le=100)
    allow_new_positions: Optional[bool] = False
    overrides: Optional[RebalanceOverrides] = None


class RebalanceOrderPreview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    side: Literal["buy", "sell"]
    qty: float
    notional: float
    estimated_price: float


class RebalanceSubmitResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    side: Literal["buy", "sell"]
    qty: float
    notional: float
    estimated_price: float
    order_id: Optional[str] = None
    status: Literal["submitted", "failed"]
    error: Optional[str] = None


class PortfolioRebalanceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    env: EnvLiteral
    mode: Literal["dry_run", "execute"]
    rebalance_id: str
    status: Literal["preview", "submitted"]
    orders: List[RebalanceOrderPreview]
    submitted: Optional[List[RebalanceSubmitResult]] = None
    alpaca_positions: Optional[List[PositionItem]] = None


class RebalanceTargetItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy_id: str
    target_weight_pct: float
    target_cash_pct: float
    updated_at: str


class PortfolioRebalanceTargetsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    env: EnvLiteral
    items: List[RebalanceTargetItem]


class ActivityItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["order", "trade", "alert", "bot_run"]
    id: str
    t: str
    data: Dict[str, Any]


class PortfolioActivityResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    env: EnvLiteral
    items: List[ActivityItem]
    next_cursor: Optional[str] = None


PortfolioOverviewResponse.model_rebuild()
