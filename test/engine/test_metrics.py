"""engine/backtest/metrics.py 테스트."""
from __future__ import annotations

import math

import pytest

from engine.backtest.metrics import (
    compute_drawdown,
    compute_metrics,
    compute_returns,
)


# ── compute_returns ──────────────────────────────────────────────────

class TestComputeReturns:
    def test_normal(self, rising_curve):
        rets = compute_returns(rising_curve)
        assert len(rets) == len(rising_curve) - 1
        for r in rets:
            assert r["ret"] > 0

    def test_empty(self):
        assert compute_returns([]) == []

    def test_single_point(self):
        # 포인트 1개는 기준값만 있으므로 수익률 없음
        assert compute_returns([{"date": "2024-01-01", "equity": 10_000}]) == []

    def test_flat_returns_zero(self, flat_curve):
        rets = compute_returns(flat_curve)
        for r in rets:
            assert r["ret"] == pytest.approx(0.0)

    def test_declining_returns_negative(self, declining_curve):
        rets = compute_returns(declining_curve)
        for r in rets:
            assert r["ret"] < 0

    def test_known_value(self):
        curve = [
            {"date": "2024-01-01", "equity": 10_000},
            {"date": "2024-01-02", "equity": 11_000},
        ]
        rets = compute_returns(curve)
        assert rets[0]["ret"] == pytest.approx(0.1)

    def test_50_pct_drop(self):
        curve = [
            {"date": "2024-01-01", "equity": 10_000},
            {"date": "2024-01-02", "equity": 5_000},
        ]
        rets = compute_returns(curve)
        assert rets[0]["ret"] == pytest.approx(-0.5)


# ── compute_drawdown ─────────────────────────────────────────────────

class TestComputeDrawdown:
    def test_all_rising_no_drawdown(self, rising_curve):
        dd = compute_drawdown(rising_curve)
        assert len(dd) == len(rising_curve)
        for d in dd:
            assert d["dd_pct"] == pytest.approx(0.0, abs=1e-9)

    def test_flat_no_drawdown(self, flat_curve):
        dd = compute_drawdown(flat_curve)
        for d in dd:
            assert d["dd_pct"] == pytest.approx(0.0, abs=1e-9)

    def test_mdd_50_pct(self, declining_curve):
        dd = compute_drawdown(declining_curve)
        mdd = min(d["dd_pct"] for d in dd)
        assert mdd == pytest.approx(-50.0, abs=0.1)

    def test_recovery_curve(self, recovery_curve):
        dd = compute_drawdown(recovery_curve)
        mdd = min(d["dd_pct"] for d in dd)
        # 10000 → 8000은 -20% MDD
        assert mdd == pytest.approx(-20.0, abs=0.1)
        # 완전 회복 후 마지막 포인트 dd는 0
        assert dd[-1]["dd_pct"] == pytest.approx(0.0, abs=1e-9)

    def test_empty(self):
        assert compute_drawdown([]) == []

    def test_single_point(self):
        dd = compute_drawdown([{"date": "2024-01-01", "equity": 10_000}])
        assert dd[0]["dd_pct"] == pytest.approx(0.0)

    def test_new_high_resets_dd(self):
        # 하락 후 신고점 갱신 → dd 다시 0
        curve = [
            {"date": "2024-01-01", "equity": 10_000},
            {"date": "2024-01-02", "equity": 9_000},
            {"date": "2024-01-03", "equity": 12_000},
        ]
        dd = compute_drawdown(curve)
        assert dd[2]["dd_pct"] == pytest.approx(0.0)


# ── compute_metrics ──────────────────────────────────────────────────

class TestComputeMetrics:
    def test_empty_curve_returns_zeros(self):
        m = compute_metrics([])
        assert m["total_return_pct"] == pytest.approx(0.0)
        assert m["cagr_pct"] == pytest.approx(0.0)
        assert m["sharpe"] == pytest.approx(0.0)

    def test_flat_curve(self, flat_curve):
        m = compute_metrics(flat_curve)
        assert m["total_return_pct"] == pytest.approx(0.0)
        assert m["sharpe"] == pytest.approx(0.0)  # std=0 → sharpe=0
        assert m["volatility_pct"] == pytest.approx(0.0)

    def test_positive_return(self, rising_curve):
        m = compute_metrics(rising_curve)
        assert m["total_return_pct"] > 0
        assert m["cagr_pct"] > 0
        assert m["sharpe"] > 0
        assert m["max_drawdown_pct"] == pytest.approx(0.0, abs=1e-9)

    def test_mdd_negative(self, declining_curve):
        m = compute_metrics(declining_curve)
        assert m["total_return_pct"] < 0
        assert m["max_drawdown_pct"] < 0

    def test_total_return_10pct(self):
        curve = [
            {"date": "2024-01-01", "equity": 10_000},
            {"date": "2024-01-02", "equity": 11_000},
        ]
        m = compute_metrics(curve)
        assert m["total_return_pct"] == pytest.approx(10.0)

    def test_benchmark_alpha_beta(self):
        # 전략과 벤치마크가 동일하면 alpha=0, beta≈1
        curve = [{"date": f"2024-01-{i+1:02d}", "equity": 10_000 + i * 50} for i in range(20)]
        bench = curve.copy()
        m = compute_metrics(curve, benchmark_curve=bench)
        assert m["alpha_pct"] == pytest.approx(0.0, abs=0.5)
        assert m["beta"] == pytest.approx(1.0, abs=0.05)
        assert m["tracking_error_pct"] == pytest.approx(0.0, abs=0.1)

    def test_benchmark_outperform(self):
        # 전략의 일간 수익률이 벤치마크보다 일관되게 높으면 alpha > 0
        # 복리 수익률(1+r)^n 방식으로 구성해야 alpha 계산이 양수가 됨
        n = 100
        strat = [{"date": f"2024-01-01", "equity": 10_000 * (1.002 ** i)} for i in range(n)]
        bench = [{"date": f"2024-01-01", "equity": 10_000 * (1.001 ** i)} for i in range(n)]
        for i, (s, b) in enumerate(zip(strat, bench)):
            s["date"] = b["date"] = f"2024-{(i//30)+1:02d}-{(i%30)+1:02d}"
        m = compute_metrics(strat, benchmark_curve=bench)
        assert m["alpha_pct"] > 0

    def test_turnover_pct_passthrough(self, rising_curve):
        m = compute_metrics(rising_curve, turnover_pct=15.5)
        assert m["turnover_pct"] == pytest.approx(15.5)

    def test_keys_present(self, rising_curve):
        m = compute_metrics(rising_curve)
        expected_keys = {
            "total_return_pct", "cagr_pct", "volatility_pct", "sharpe",
            "max_drawdown_pct", "alpha_pct", "beta", "tracking_error_pct",
            "information_ratio", "turnover_pct",
        }
        assert expected_keys <= set(m.keys())

    def test_no_nan_values(self, rising_curve):
        m = compute_metrics(rising_curve)
        for k, v in m.items():
            assert not math.isnan(v), f"{k} is NaN"
