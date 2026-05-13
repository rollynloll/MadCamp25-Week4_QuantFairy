from __future__ import annotations

from datetime import datetime, time
from typing import Optional

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # type: ignore

_ET = ZoneInfo("America/New_York")
_MARKET_OPEN = time(9, 30)
_MARKET_CLOSE = time(16, 0)


def is_within_market_hours(dt: Optional[datetime] = None) -> bool:
    """현재(또는 지정한) 시각이 미국 장 시간(09:30–16:00 ET, 평일) 내인지 확인한다."""
    now = (dt or datetime.now(tz=_ET)).astimezone(_ET)
    if now.weekday() >= 5:
        return False
    return _MARKET_OPEN <= now.time() < _MARKET_CLOSE


def assert_market_hours(dt: Optional[datetime] = None) -> None:
    """장 시간 외이면 MarketClosedError를 발생시킨다."""
    from engine.errors import MarketClosedError
    if not is_within_market_hours(dt):
        now = (dt or datetime.now(tz=_ET)).astimezone(_ET)
        raise MarketClosedError(
            f"Market closed at {now.strftime('%Y-%m-%d %H:%M %Z')} "
            f"(hours: 09:30–16:00 ET, Mon–Fri)"
        )
