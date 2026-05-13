from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import List, Tuple
from zoneinfo import ZoneInfo


_KST = ZoneInfo("Asia/Seoul")


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _now_kst() -> datetime:
    return datetime.now(tz=_KST)


def sanitize_equity_curve(points: List[dict]) -> List[dict]:
    """시간순 정렬, NaN/Inf/None 제거, 양수 포인트만 존재하면 0 제거."""
    cleaned: List[dict] = []
    for point in sorted(points, key=lambda p: str(p.get("t", ""))):
        ts = point.get("t")
        if ts is None:
            continue
        equity = point.get("equity", 0.0)
        try:
            equity = float(equity)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(equity):
            continue
        cleaned.append({"t": str(ts), "equity": equity})

    if any(p["equity"] > 0 for p in cleaned):
        cleaned = [p for p in cleaned if p["equity"] > 0]
    return cleaned


def downsample_equity_to_hourly(points: List[dict]) -> List[dict]:
    """분봉 equity curve를 시간봉으로 다운샘플링한다."""
    if not points:
        return []
    bucketed: dict[str, dict] = {}
    for point in points:
        ts = point.get("t")
        if ts is None:
            continue
        try:
            dt = _parse_dt(str(ts))
        except (ValueError, TypeError):
            continue
        key = dt.replace(minute=0, second=0, microsecond=0).isoformat()
        bucketed[key] = point
    downsampled = sorted(bucketed.values(), key=lambda p: str(p.get("t", "")))
    return sanitize_equity_curve(downsampled)


def ensure_latest_equity_point(
    equity_curve: List[dict],
    latest_equity: float,
    *,
    now_dt: datetime | None = None,
) -> Tuple[List[dict], bool]:
    """마지막 포인트가 최신 자산값과 다르면 현재 시각 포인트를 추가한다.

    Returns:
        (updated_curve, was_appended)
    """
    if latest_equity <= 0:
        return equity_curve, False
    now_dt = now_dt or _now_kst()
    now_iso = now_dt.isoformat()
    if not equity_curve:
        return [{"t": now_iso, "equity": latest_equity}], True

    last_point = equity_curve[-1]
    try:
        last_equity = float(last_point.get("equity", latest_equity))
    except (TypeError, ValueError):
        last_equity = latest_equity
    last_ts = last_point.get("t")
    last_dt: datetime | None = None
    if last_ts is not None:
        try:
            last_dt = _parse_dt(str(last_ts))
        except (ValueError, TypeError):
            last_dt = None

    should_append = abs(last_equity - latest_equity) > 0.01
    if last_dt is not None and last_dt.date() < now_dt.date():
        should_append = True
    if not should_append:
        return equity_curve, False
    return [*equity_curve, {"t": now_iso, "equity": latest_equity}], True
