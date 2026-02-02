from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


StrategyKind = Literal["template", "python"]


class UniverseSpec(BaseModel):
    """Define the investable universe for a strategy."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["CUSTOM", "PRESET", "SECTOR", "INDEX"] = "CUSTOM"
    symbols: Optional[List[str]] = None
    preset_id: Optional[str] = None
    sector: Optional[str] = None
    max_n: Optional[int] = None


class RebalanceSpec(BaseModel):
    """Rebalance frequency configuration."""

    model_config = ConfigDict(extra="forbid")

    freq: Literal["daily", "weekly", "monthly"] = "monthly"
    trading_day: Optional[int] = None


class ExecutionSpec(BaseModel):
    """Execution assumptions for backtests."""

    model_config = ConfigDict(extra="forbid")

    fee_bps: float = 0.0
    slippage_bps: float = 0.0
    order_type: Literal["market", "limit"] = "market"


class RiskSpec(BaseModel):
    """Risk constraints for portfolio construction."""

    model_config = ConfigDict(extra="forbid")

    max_weight_per_asset: float = 1.0
    cash_buffer: float = 0.0
    long_only: bool = True
    max_turnover: Optional[float] = None


class TemplateBody(BaseModel):
    """Template strategy definition used by UI or presets."""

    model_config = ConfigDict(extra="forbid")

    template_type: str
    params: Dict[str, Any] = Field(default_factory=dict)


class PythonPermissions(BaseModel):
    """Permissions for user-provided python strategies."""

    model_config = ConfigDict(extra="forbid")

    network: bool = False
    filesystem: bool = False


class PythonBody(BaseModel):
    """User-supplied python strategy (sandboxed)."""

    model_config = ConfigDict(extra="forbid")

    entrypoint: str
    code: str
    requirements: List[str] = Field(default_factory=list)
    permissions: PythonPermissions = Field(default_factory=PythonPermissions)


class StrategySpec(BaseModel):
    """Unified strategy specification.

    Params merging rule:
    - ctx.params overrides spec.template.params when both are present.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    version: str
    kind: StrategyKind
    universe: UniverseSpec = Field(default_factory=UniverseSpec)
    rebalance: RebalanceSpec = Field(default_factory=RebalanceSpec)
    execution: ExecutionSpec = Field(default_factory=ExecutionSpec)
    risk: RiskSpec = Field(default_factory=RiskSpec)
    template: Optional[TemplateBody] = None
    python: Optional[PythonBody] = None

    @model_validator(mode="after")
    def _validate_kind(self) -> "StrategySpec":
        if self.kind == "template" and not self.template:
            raise ValueError("template body required when kind='template'")
        if self.kind == "python" and not self.python:
            raise ValueError("python body required when kind='python'")
        return self


DEFAULT_TEMPLATE_PARAMS: Dict[str, Dict[str, Any]] = {
    "momentum_topn": {"lookback_days": 252, "top_n": 10, "rebalance": "monthly"},
    "rsi_mean_reversion": {"rsi_window": 14, "entry_rsi": 30, "exit_rsi": 50},
    "trend_sma200": {"sma_window": 200, "benchmark_symbol": "SPY"},
    "low_volatility": {"lookback_days": 60, "top_k": 10, "weighting": "inverse_vol"},
    "vol_adj_momentum": {"lookback_days": 252, "vol_window": 60, "top_k": 10},
    "risk_on_off": {"benchmark_symbol": "SPY", "sma_window": 200, "top_k": 10},
}


def _deep_merge(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def create_strategy_spec(template_type: str, overrides: Dict[str, Any]) -> StrategySpec:
    """Create a fully-populated StrategySpec from a template type.

    `overrides` supports nested updates for fields like `risk`, `rebalance`, etc.
    """

    base = {
        "id": f"tpl_{template_type}",
        "name": template_type.replace("_", " ").title(),
        "version": "1.0.0",
        "kind": "template",
        "template": {
            "template_type": template_type,
            "params": DEFAULT_TEMPLATE_PARAMS.get(template_type, {}),
        },
    }
    payload = _deep_merge(base, overrides or {})
    return StrategySpec.model_validate(payload)
