from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import yaml

from engine.strategies.registry import list_entrypoints

VALID_UNIVERSES = {"snp500", "sector_etf"}
VALID_REBALANCES = {"daily", "weekly", "monthly"}


@dataclass
class BotConfig:
    name: str
    strategy: str
    universe: str
    capital_pct: float
    rebalance: str
    params: dict = field(default_factory=dict)


@dataclass
class RiskConfig:
    daily_loss_limit_pct: float = 0.05
    max_drawdown_pct: float = 0.20


@dataclass
class BotsConfig:
    bots: List[BotConfig]
    risk: RiskConfig


def load_bots_config(path: Path) -> BotsConfig:
    if not path.exists():
        raise FileNotFoundError(f"bots.yaml를 찾을 수 없습니다: {path}")
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    bots = [
        BotConfig(
            name=b["name"],
            strategy=b["strategy"],
            universe=b["universe"],
            capital_pct=float(b["capital_pct"]),
            rebalance=b.get("rebalance", "monthly"),
            params=b.get("params", {}),
        )
        for b in raw.get("bots", [])
    ]

    r = raw.get("risk", {})
    risk = RiskConfig(
        daily_loss_limit_pct=float(r.get("daily_loss_limit_pct", 0.05)),
        max_drawdown_pct=float(r.get("max_drawdown_pct", 0.20)),
    )

    return BotsConfig(bots=bots, risk=risk)


def validate_bots_config(config: BotsConfig) -> None:
    valid_strategies = set(list_entrypoints())
    errors: List[str] = []

    total_pct = sum(b.capital_pct for b in config.bots)
    if total_pct > 1.0 + 1e-9:
        errors.append(f"capital_pct 합계가 1.0을 초과합니다: {total_pct:.3f}")

    seen_names: set = set()
    for b in config.bots:
        if b.name in seen_names:
            errors.append(f"중복된 봇 이름: {b.name!r}")
        seen_names.add(b.name)

        if b.strategy not in valid_strategies:
            errors.append(
                f"봇 {b.name!r}: 알 수 없는 전략 {b.strategy!r}. "
                f"사용 가능: {sorted(valid_strategies)}"
            )
        if b.universe not in VALID_UNIVERSES:
            errors.append(
                f"봇 {b.name!r}: 알 수 없는 유니버스 {b.universe!r}. "
                f"사용 가능: {sorted(VALID_UNIVERSES)}"
            )
        if b.rebalance not in VALID_REBALANCES:
            errors.append(
                f"봇 {b.name!r}: 알 수 없는 리밸런싱 주기 {b.rebalance!r}. "
                f"사용 가능: {sorted(VALID_REBALANCES)}"
            )
        if not (0.0 < b.capital_pct <= 1.0):
            errors.append(
                f"봇 {b.name!r}: capital_pct는 0 < pct <= 1.0 이어야 합니다: {b.capital_pct}"
            )

    if errors:
        raise ValueError("bots.yaml 검증 실패:\n" + "\n".join(f"  - {e}" for e in errors))
