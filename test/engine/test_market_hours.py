"""engine/trading/market_hours.py 테스트 — US 장 시간 체크."""
from __future__ import annotations

from datetime import datetime

import pytest

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

from engine.errors import MarketClosedError
from engine.trading.market_hours import assert_market_hours, is_within_market_hours

_ET = ZoneInfo("America/New_York")


def _dt(year: int, month: int, day: int, hour: int, minute: int = 0) -> datetime:
    """ET 기준 datetime 생성 헬퍼."""
    return datetime(year, month, day, hour, minute, tzinfo=_ET)


# ── is_within_market_hours ───────────────────────────────────────────

class TestIsWithinMarketHours:
    # 정상 개장 시간
    def test_morning_open_true(self):
        assert is_within_market_hours(_dt(2024, 5, 7, 10, 0)) is True

    def test_just_after_open_true(self):
        assert is_within_market_hours(_dt(2024, 5, 7, 9, 30)) is True

    def test_midday_true(self):
        assert is_within_market_hours(_dt(2024, 5, 7, 13, 0)) is True

    def test_one_minute_before_close_true(self):
        assert is_within_market_hours(_dt(2024, 5, 7, 15, 59)) is True

    # 장 외 시간
    def test_before_open_false(self):
        assert is_within_market_hours(_dt(2024, 5, 7, 9, 29)) is False

    def test_at_close_false(self):
        # 16:00 정각은 장 마감 후 → False
        assert is_within_market_hours(_dt(2024, 5, 7, 16, 0)) is False

    def test_after_close_false(self):
        assert is_within_market_hours(_dt(2024, 5, 7, 17, 30)) is False

    def test_midnight_false(self):
        assert is_within_market_hours(_dt(2024, 5, 7, 0, 0)) is False

    def test_early_morning_false(self):
        assert is_within_market_hours(_dt(2024, 5, 7, 4, 0)) is False

    # 주말
    def test_saturday_false(self):
        # 2024-05-11 = 토요일
        assert is_within_market_hours(_dt(2024, 5, 11, 12, 0)) is False

    def test_sunday_false(self):
        # 2024-05-12 = 일요일
        assert is_within_market_hours(_dt(2024, 5, 12, 12, 0)) is False

    # 경계값
    def test_exactly_9_30_true(self):
        assert is_within_market_hours(_dt(2024, 5, 7, 9, 30)) is True

    def test_exactly_16_00_false(self):
        assert is_within_market_hours(_dt(2024, 5, 7, 16, 0)) is False

    def test_monday_open_true(self):
        # 2024-05-06 = 월요일
        assert is_within_market_hours(_dt(2024, 5, 6, 11, 0)) is True

    def test_friday_close_works(self):
        # 2024-05-10 = 금요일 정상 개장
        assert is_within_market_hours(_dt(2024, 5, 10, 14, 0)) is True


# ── assert_market_hours ──────────────────────────────────────────────

class TestAssertMarketHours:
    def test_raises_when_closed_weekend(self):
        with pytest.raises(MarketClosedError):
            assert_market_hours(_dt(2024, 5, 11, 12, 0))  # 토요일

    def test_raises_before_open(self):
        with pytest.raises(MarketClosedError):
            assert_market_hours(_dt(2024, 5, 7, 8, 0))

    def test_raises_after_close(self):
        with pytest.raises(MarketClosedError):
            assert_market_hours(_dt(2024, 5, 7, 16, 1))

    def test_does_not_raise_when_open(self):
        # 예외가 발생하지 않아야 함
        assert_market_hours(_dt(2024, 5, 7, 10, 0))

    def test_error_message_contains_time_info(self):
        with pytest.raises(MarketClosedError, match=r"2024"):
            assert_market_hours(_dt(2024, 5, 11, 12, 0))

    def test_market_closed_error_is_runtime_error(self):
        err = MarketClosedError("test")
        assert isinstance(err, RuntimeError)
