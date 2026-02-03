from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Protocol

import pandas as pd

from app.strategies.spec import StrategySpec


@dataclass
class StrategyContext:
    my_strategy_id: str
    user_id: str
    params: Dict
    code_version: str
    state: Dict = field(default_factory=dict)
    spec: StrategySpec | None = None

    def resolved_params(self) -> Dict:
        """Return merged params, with ctx.params overriding spec.template.params."""
        spec_params = {}
        if self.spec and self.spec.kind == "template" and self.spec.template:
            spec_params = self.spec.template.params or {}
        return {**spec_params, **(self.params or {})}


@dataclass
class StrategySignal:
    date: str
    target_weights: Dict[str, float]


class Strategy(Protocol):
    """Strategy interface used by the backtest runner."""

    name: str

    def required_columns(self) -> List[str]:
        """Return required price columns (e.g. ['adj_close'])."""
        ...

    def generate_signals(
        self,
        prices: pd.DataFrame,
        ctx: StrategyContext,
        universe: List[str],
    ) -> Iterable[StrategySignal]:
        """Yield target allocations for rebalance dates."""
        ...

    def compute_target_weights(
        self,
        prices: pd.DataFrame,
        ctx: StrategyContext,
        universe: List[str],
        dt: pd.Timestamp,
    ) -> Dict[str, float]:
        """Preferred interface: compute weights for a given rebalance date."""
        raise NotImplementedError
