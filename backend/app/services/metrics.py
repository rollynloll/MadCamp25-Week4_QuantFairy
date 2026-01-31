from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple


def compute_returns(equity_curve: List[Dict[str, float]]) -> List[Dict[str, float]]:
    returns: List[Dict[str, float]] = []
    prev = None
    for point in equity_curve:
        equity = point["equity"]
        if prev is None:
            prev = equity
            continue
        ret = (equity / prev - 1.0) if prev else 0.0
        returns.append({"date": point["date"], "ret": ret})
        prev = equity
    return returns


def compute_drawdown(equity_curve: List[Dict[str, float]]) -> List[Dict[str, float]]:
    drawdown: List[Dict[str, float]] = []
    peak = None
    for point in equity_curve:
        equity = point["equity"]
        if peak is None or equity > peak:
            peak = equity
        dd = (equity - peak) / peak * 100 if peak else 0.0
        drawdown.append({"date": point["date"], "dd_pct": dd})
    return drawdown


def _stats(returns: List[float]) -> Tuple[float, float]:
    if not returns:
        return 0.0, 0.0
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / len(returns)
    return mean, math.sqrt(var)


def compute_metrics(
    equity_curve: List[Dict[str, float]],
    benchmark_curve: Optional[List[Dict[str, float]]] = None,
    turnover_pct: float = 0.0,
) -> Dict[str, float]:
    if not equity_curve:
        return {
            "total_return_pct": 0.0,
            "cagr_pct": 0.0,
            "volatility_pct": 0.0,
            "sharpe": 0.0,
            "max_drawdown_pct": 0.0,
            "alpha_pct": 0.0,
            "beta": 0.0,
            "tracking_error_pct": 0.0,
            "information_ratio": 0.0,
            "turnover_pct": turnover_pct,
        }

    total_return_pct = (equity_curve[-1]["equity"] / equity_curve[0]["equity"] - 1) * 100
    returns = [item["ret"] for item in compute_returns(equity_curve)]
    mean, std = _stats(returns)
    volatility_pct = std * math.sqrt(252) * 100 if std else 0.0
    sharpe = (mean / std * math.sqrt(252)) if std else 0.0

    periods = max(len(returns), 1)
    cagr_pct = ((equity_curve[-1]["equity"] / equity_curve[0]["equity"]) ** (252 / periods) - 1) * 100

    drawdown = compute_drawdown(equity_curve)
    max_drawdown_pct = min((d["dd_pct"] for d in drawdown), default=0.0)

    alpha_pct = 0.0
    beta = 0.0
    tracking_error_pct = 0.0
    information_ratio = 0.0

    if benchmark_curve:
        bench_returns = [item["ret"] for item in compute_returns(benchmark_curve)]
        if bench_returns:
            mean_b, std_b = _stats(bench_returns)
            cov = sum(
                (r - mean) * (b - mean_b)
                for r, b in zip(returns, bench_returns)
            ) / len(bench_returns)
            beta = cov / (std_b ** 2) if std_b else 0.0
            alpha_pct = ((mean - beta * mean_b) * 252) * 100
            diff = [r - b for r, b in zip(returns, bench_returns)]
            mean_diff, std_diff = _stats(diff)
            tracking_error_pct = std_diff * math.sqrt(252) * 100 if std_diff else 0.0
            information_ratio = (
                mean_diff / std_diff * math.sqrt(252) if std_diff else 0.0
            )

    return {
        "total_return_pct": total_return_pct,
        "cagr_pct": cagr_pct,
        "volatility_pct": volatility_pct,
        "sharpe": sharpe,
        "max_drawdown_pct": max_drawdown_pct,
        "alpha_pct": alpha_pct,
        "beta": beta,
        "tracking_error_pct": tracking_error_pct,
        "information_ratio": information_ratio,
        "turnover_pct": turnover_pct,
    }
