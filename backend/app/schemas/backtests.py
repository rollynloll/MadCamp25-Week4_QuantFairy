from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    reason: str


class UniverseSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["PRESET", "CUSTOM"]
    preset_id: Optional[str] = None
    tickers: Optional[List[str]] = None


class BacktestSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    period_start: str
    period_end: str
    timeframe: Literal["1D"]
    initial_cash: float
    fee_bps: float
    slippage_bps: float
    rebalance: Literal["daily", "weekly", "monthly"]
    universe: UniverseSpec
    price_field: Literal["adj_close", "close"] = "adj_close"
    currency: Literal["USD"] = "USD"


class StrategyRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["public", "my"]
    id: str
    params_override: Optional[Dict[str, Any]] = None
    label: Optional[str] = None


class BenchmarkRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    label: Optional[str] = None


class EnsembleConstraints(BaseModel):
    model_config = ConfigDict(extra="forbid")

    normalize_weights: bool = True
    max_weight_per_symbol: Optional[float] = None
    max_positions: Optional[int] = None
    cash_buffer_pct: Optional[float] = None
    min_trade_weight: Optional[float] = None


class EnsembleSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mixing: Literal["weighted_sum"]
    weights: Dict[str, float]
    constraints: Optional[EnsembleConstraints] = None


class BacktestCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["single", "batch", "ensemble"]
    spec: BacktestSpec
    strategies: List[StrategyRef]
    benchmarks: Optional[List[BenchmarkRef]] = None
    ensemble: Optional[EnsembleSpec] = None


class Metrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_return_pct: float
    cagr_pct: float
    volatility_pct: float
    sharpe: float
    max_drawdown_pct: float
    alpha_pct: float
    beta: float
    tracking_error_pct: float
    information_ratio: float
    turnover_pct: float


class SeriesPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: str
    value: float


class BacktestResultItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    strategy_ref: StrategyRef
    metrics: Metrics
    equity_curve: List[Dict[str, Any]]
    returns: List[Dict[str, Any]]
    drawdown: List[Dict[str, Any]]
    positions_summary: Dict[str, Any]


class BacktestJob(BaseModel):
    model_config = ConfigDict(extra="forbid")

    backtest_id: str
    mode: Literal["single", "batch", "ensemble"]
    status: Literal["queued", "running", "done", "failed", "canceled"]
    spec: BacktestSpec
    strategies: List[StrategyRef]
    benchmarks: Optional[List[BenchmarkRef]] = None
    created_at: str
    updated_at: str


class BacktestListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: List[BacktestJob]
    next_cursor: Optional[str] = None


class BacktestResultsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    backtest_id: str
    status: str
    benchmarks: Optional[Dict[str, Any]] = None
    results: Optional[List[BacktestResultItem]] = None
    comparison_table: Optional[List[Dict[str, Any]]] = None
    ensemble_result: Optional[BacktestResultItem] = None
    components: Optional[List[BacktestResultItem]] = None


class BacktestValidateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valid: bool
    errors: List[ErrorDetail]
