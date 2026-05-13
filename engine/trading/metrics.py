from __future__ import annotations

from typing import Any, Dict, List


def compute_strategy_runtime_metrics(
    position_rows: List[Dict[str, Any]],
) -> Dict[str, Dict[str, float | int]]:
    """포지션 목록 → 전략별 런타임 지표 집계.

    Args:
        position_rows: 각 행은 strategy_id(또는 user_strategy_id), qty,
                       avg_entry_price, unrealized_pnl(또는 unrealized_pl) 필드를 가진다.

    Returns:
        {strategy_id: {positions_count, pnl_today_value, pnl_today_pct, managed_value}}
    """
    metrics: Dict[str, Dict[str, float | int]] = {}
    for row in position_rows:
        strategy_id = row.get("strategy_id") or row.get("user_strategy_id")
        if not strategy_id:
            continue
        key = str(strategy_id)
        try:
            qty = abs(float(row.get("qty", 0.0) or 0.0))
        except (TypeError, ValueError):
            qty = 0.0
        try:
            avg_entry_price = float(row.get("avg_entry_price", 0.0) or 0.0)
        except (TypeError, ValueError):
            avg_entry_price = 0.0
        try:
            unrealized_pnl = float(
                row.get("unrealized_pnl", row.get("unrealized_pl", 0.0)) or 0.0
            )
        except (TypeError, ValueError):
            unrealized_pnl = 0.0

        exposure_value = abs(qty * avg_entry_price)
        item = metrics.setdefault(
            key,
            {"positions_count": 0, "pnl_today_value": 0.0, "pnl_today_pct": 0.0, "managed_value": 0.0},
        )
        if qty > 0:
            item["positions_count"] = int(item["positions_count"]) + 1
        item["pnl_today_value"] = float(item["pnl_today_value"]) + unrealized_pnl
        item["managed_value"] = float(item["managed_value"]) + exposure_value

    for item in metrics.values():
        managed = float(item.get("managed_value", 0.0) or 0.0)
        pnl = float(item.get("pnl_today_value", 0.0) or 0.0)
        item["pnl_today_pct"] = (pnl / managed * 100.0) if managed > 0 else 0.0
    return metrics
