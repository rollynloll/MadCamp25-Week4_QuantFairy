from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    reason: str


class PaginationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: List[Any]
    next_cursor: Optional[str] = None


class AuthorBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    type: Literal["official", "community"]


class SampleMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pnl_amount: float
    pnl_pct: float
    sharpe: float
    max_drawdown_pct: float
    win_rate_pct: float


class SampleTradeStats(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trades_count: float
    avg_hold_hours: float


class Popularity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    adds_count: float
    likes_count: float
    runs_count: float


class PublicStrategyListItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    public_strategy_id: str
    name: str
    one_liner: str
    category: str
    tags: List[str]
    risk_level: Literal["low", "mid", "high"]
    version: str
    author: AuthorBlock
    sample_metrics: SampleMetrics
    sample_trade_stats: SampleTradeStats
    popularity: Popularity
    supported_assets: List[str]
    supported_timeframes: List[str]
    created_at: str
    updated_at: str


class RulesBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    signal_definition: str
    entry_rules: str
    exit_rules: str
    rebalance_rule: str
    position_sizing: str
    risk_management: str


class RequirementsBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    universe: Dict[str, Any]
    data: Dict[str, Any]


class SampleBacktestSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    period_start: str
    period_end: str
    timeframe: str
    universe_used: str
    initial_cash: float
    fee_bps: float
    slippage_bps: float


class SamplePerformance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metrics: Dict[str, Any]
    equity_curve: List[Dict[str, Any]]


class PublicStrategyDetail(PublicStrategyListItem):
    model_config = ConfigDict(extra="forbid")

    full_description: str
    thesis: str
    rules: RulesBlock
    param_schema: Dict[str, Any]
    default_params: Dict[str, Any]
    recommended_presets: List[Dict[str, Any]]
    requirements: RequirementsBlock
    sample_backtest_spec: SampleBacktestSpec
    sample_performance: SamplePerformance
    known_failure_modes: List[str]
    risk_disclaimer: str


class ValidateParamsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    params: Dict[str, Any]


class ValidateParamsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valid: bool
    errors: List[ErrorDetail]


class MyStrategy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    my_strategy_id: str
    name: str
    source_public_strategy_id: str
    public_version_snapshot: str
    params: Dict[str, Any]
    note: Optional[str] = None
    created_at: str
    updated_at: str


class CreateMyStrategyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_public_strategy_id: str
    name: Optional[str] = None
    params: Dict[str, Any]
    note: Optional[str] = None


class UpdateMyStrategyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    note: Optional[str] = None


class MyStrategyDetailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    my_strategy: MyStrategy
    public_strategy_brief: Dict[str, Any]


class CloneMyStrategyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    params_overrides: Dict[str, Any] = Field(default_factory=dict)


class UpgradeMyStrategyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_public_version: str
    auto_migrate_params: bool
