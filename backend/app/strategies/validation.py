from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Dict, List


@dataclass
class StrategyValidationError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


def validate_target_weights(
    weights: Dict[str, float],
    universe: List[str],
    long_only: bool,
    cash_buffer: float,
    max_weight_per_asset: float,
) -> Dict[str, float]:
    """Validate and normalize target weights.

    - Removes NaN/inf entries
    - Enforces symbol membership
    - Enforces long-only and max weight per asset
    - Normalizes total weights to <= 1 - cash_buffer
    """

    if weights is None:
        return {}

    allowed = {s.upper() for s in universe}
    cleaned: Dict[str, float] = {}

    for symbol, raw in weights.items():
        if symbol is None:
            continue
        symbol_norm = str(symbol).upper()
        if symbol_norm not in allowed:
            raise StrategyValidationError(f"Symbol not in universe: {symbol_norm}")
        if raw is None:
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(value):
            continue
        if long_only and value < 0:
            raise StrategyValidationError(f"Negative weight not allowed: {symbol_norm}")
        if max_weight_per_asset is not None and max_weight_per_asset > 0:
            value = min(value, max_weight_per_asset)
        if value == 0:
            continue
        cleaned[symbol_norm] = value

    total = sum(cleaned.values())
    if total <= 0:
        return {}

    max_total = max(0.0, 1.0 - max(cash_buffer, 0.0))
    if total > max_total:
        scale = max_total / total
        cleaned = {k: v * scale for k, v in cleaned.items()}

    return cleaned
