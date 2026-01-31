from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Protocol

import pandas as pd


@dataclass
class StrategyContext:
    my_strategy_id: str
    user_id: str
    params: Dict
    code_version: str


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
