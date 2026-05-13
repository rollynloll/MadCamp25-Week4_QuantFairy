"""engine/strategies/registry.py 테스트 — 전략 레지스트리."""
from __future__ import annotations

import pytest

from engine.strategies.registry import get_strategy, list_entrypoints

_SHORT_KEYS = [
    "momentum",
    "trend",
    "rsi-reversion",
    "low-vol",
    "vol-momentum",
    "risk-on-off",
]

_LONG_KEYS = [
    "momentum_topn_v1",
    "trend_sma200_v1",
    "rsi_mean_reversion_v1",
    "low_volatility",
    "vol_adj_momentum",
    "risk_on_off",
]


# ── get_strategy ─────────────────────────────────────────────────────

class TestGetStrategy:
    @pytest.mark.parametrize("key", _SHORT_KEYS)
    def test_short_keys_return_strategy(self, key):
        strategy = get_strategy(key)
        assert strategy is not None
        assert hasattr(strategy, "name")

    @pytest.mark.parametrize("key", _LONG_KEYS)
    def test_long_keys_return_strategy(self, key):
        strategy = get_strategy(key)
        assert strategy is not None

    def test_short_and_long_same_type(self):
        short = get_strategy("momentum")
        long = get_strategy("momentum_topn_v1")
        assert type(short) is type(long)

    def test_trend_short_long_same(self):
        assert type(get_strategy("trend")) is type(get_strategy("trend_sma200_v1"))

    def test_rsi_short_long_same(self):
        assert type(get_strategy("rsi-reversion")) is type(get_strategy("rsi_mean_reversion_v1"))

    def test_low_vol_short_long_same(self):
        assert type(get_strategy("low-vol")) is type(get_strategy("low_volatility"))

    def test_vol_momentum_short_long_same(self):
        assert type(get_strategy("vol-momentum")) is type(get_strategy("vol_adj_momentum"))

    def test_invalid_key_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown entrypoint"):
            get_strategy("nonexistent_strategy_xyz")

    def test_empty_string_raises_value_error(self):
        with pytest.raises(ValueError):
            get_strategy("")

    def test_each_call_returns_new_instance(self):
        a = get_strategy("momentum")
        b = get_strategy("momentum")
        assert a is not b, "get_strategy는 매번 새 인스턴스를 반환해야 한다"

    def test_strategy_has_required_attributes(self):
        for key in _SHORT_KEYS:
            s = get_strategy(key)
            assert hasattr(s, "name"), f"{key}: name 속성 없음"
            assert hasattr(s, "generate_signals") or hasattr(
                s, "compute_target_weights"
            ), f"{key}: 신호 생성 메서드 없음"


# ── list_entrypoints ─────────────────────────────────────────────────

class TestListEntrypoints:
    def test_returns_list(self):
        assert isinstance(list_entrypoints(), list)

    def test_all_short_keys_present(self):
        eps = set(list_entrypoints())
        for k in _SHORT_KEYS:
            assert k in eps, f"단축 키 {k!r}가 레지스트리에 없음"

    def test_all_long_keys_present(self):
        eps = set(list_entrypoints())
        for k in _LONG_KEYS:
            assert k in eps, f"전체 이름 키 {k!r}가 레지스트리에 없음"

    def test_no_duplicates(self):
        eps = list_entrypoints()
        assert len(eps) == len(set(eps)), "레지스트리에 중복 키가 있음"

    def test_all_keys_are_strings(self):
        for k in list_entrypoints():
            assert isinstance(k, str)
