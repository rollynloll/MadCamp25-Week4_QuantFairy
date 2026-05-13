"""engine/backtest/runner.py 통합 테스트 — BacktestRunner."""
from __future__ import annotations

import math

import pandas as pd
import pytest

from engine.backtest.runner import BacktestResult, run
from engine.errors import DataNotFoundError, DataSourceError
from engine.strategies.base import StrategyContext, StrategySignal
from engine.strategies.registry import get_strategy


# ── 헬퍼 ─────────────────────────────────────────────────────────────

def _run_simple(mock_data_provider, strategy_key="momentum", universe=None):
    """기본 설정으로 백테스트를 실행한다."""
    return run(
        strategy=get_strategy(strategy_key),
        data_provider=mock_data_provider,
        ctx=StrategyContext(params={"top_n": 2, "lookback_days": 60}),
        universe=universe or ["AAPL", "MSFT", "GOOG"],
        start_date="2022-01-03",
        end_date="2022-12-30",
        initial_cash=10_000.0,
        fee_bps=0.0,
        slippage_bps=0.0,
    )


# ── 정상 실행 ─────────────────────────────────────────────────────────

class TestRunnerNormal:
    def test_returns_backtest_result(self, mock_data_provider):
        result = _run_simple(mock_data_provider)
        assert isinstance(result, BacktestResult)

    def test_equity_curve_nonempty(self, mock_data_provider):
        result = _run_simple(mock_data_provider)
        assert len(result.equity_curve) > 0

    def test_equity_curve_starts_at_initial_cash(self, mock_data_provider):
        result = _run_simple(mock_data_provider)
        assert result.equity_curve[0]["equity"] == pytest.approx(10_000.0, rel=0.01)

    def test_equity_curve_has_date_field(self, mock_data_provider):
        result = _run_simple(mock_data_provider)
        for pt in result.equity_curve[:5]:
            assert "date" in pt
            assert "equity" in pt

    def test_metrics_keys_present(self, mock_data_provider):
        result = _run_simple(mock_data_provider)
        required = {"total_return_pct", "cagr_pct", "sharpe", "max_drawdown_pct"}
        assert required <= set(result.metrics.keys())

    def test_no_nan_in_metrics(self, mock_data_provider):
        result = _run_simple(mock_data_provider)
        for k, v in result.metrics.items():
            assert not math.isnan(v), f"metrics[{k!r}] is NaN"

    def test_trade_log_populated(self, mock_data_provider):
        result = _run_simple(mock_data_provider)
        assert len(result.trade_log) > 0
        for entry in result.trade_log:
            assert "date" in entry
            assert "equity" in entry
            assert "weights" in entry

    def test_holdings_history_populated(self, mock_data_provider):
        result = _run_simple(mock_data_provider)
        assert len(result.holdings_history) > 0

    def test_initial_cash_preserved_if_no_trades(self, mock_data_provider):
        """신호가 없는 전략은 자산이 초기 현금 근방에서 유지된다."""
        from unittest.mock import MagicMock
        strategy = MagicMock()
        strategy.compute_target_weights.return_value = {}
        result = run(
            strategy=strategy,
            data_provider=mock_data_provider,
            ctx=StrategyContext(),
            universe=["AAPL"],
            start_date="2022-01-03",
            end_date="2022-06-30",
            initial_cash=10_000.0,
        )
        # 포지션 없으면 자산은 변하지 않음
        assert result.equity_curve[-1]["equity"] == pytest.approx(10_000.0)


# ── 수수료·슬리피지 ────────────────────────────────────────────────────

class TestFeeSlippage:
    def test_fee_reduces_equity(self, mock_data_provider):
        no_fee = _run_simple(mock_data_provider)
        with_fee = run(
            strategy=get_strategy("momentum"),
            data_provider=mock_data_provider,
            ctx=StrategyContext(params={"top_n": 2, "lookback_days": 60}),
            universe=["AAPL", "MSFT", "GOOG"],
            start_date="2022-01-03",
            end_date="2022-12-30",
            initial_cash=10_000.0,
            fee_bps=50.0,  # 0.5% 수수료
        )
        # 수수료가 있으면 총 자산이 더 낮거나 같다
        assert (
            with_fee.equity_curve[-1]["equity"]
            <= no_fee.equity_curve[-1]["equity"] + 1e-6
        )


# ── 벤치마크 ──────────────────────────────────────────────────────────

class TestBenchmark:
    def test_benchmark_payload_present(self, mock_data_provider):
        result = run(
            strategy=get_strategy("momentum"),
            data_provider=mock_data_provider,
            ctx=StrategyContext(params={"top_n": 2, "lookback_days": 60}),
            universe=["AAPL", "MSFT", "GOOG"],
            start_date="2022-01-03",
            end_date="2022-12-30",
            initial_cash=10_000.0,
            benchmark_symbol="AAPL",
        )
        assert result.benchmark is not None
        assert "equity_curve" in result.benchmark
        assert "metrics" in result.benchmark

    def test_no_benchmark_payload_is_none(self, mock_data_provider):
        result = _run_simple(mock_data_provider)
        assert result.benchmark is None

    def test_cash_benchmark_treated_as_none(self, mock_data_provider):
        result = run(
            strategy=get_strategy("momentum"),
            data_provider=mock_data_provider,
            ctx=StrategyContext(params={"top_n": 2, "lookback_days": 60}),
            universe=["AAPL", "MSFT"],
            start_date="2022-01-03",
            end_date="2022-12-30",
            initial_cash=10_000.0,
            benchmark_symbol="CASH",
        )
        assert result.benchmark is None


# ── 에러 케이스 ───────────────────────────────────────────────────────

class TestRunnerErrors:
    def test_empty_price_data_raises_data_not_found(self):
        from unittest.mock import MagicMock
        provider = MagicMock()
        provider.get_prices.return_value = pd.DataFrame()

        with pytest.raises(DataNotFoundError):
            run(
                strategy=get_strategy("momentum"),
                data_provider=provider,
                ctx=StrategyContext(),
                universe=["FAKE1", "FAKE2"],
                start_date="2022-01-03",
                end_date="2022-12-30",
            )

    def test_provider_exception_raises_data_source_error(self):
        from unittest.mock import MagicMock
        provider = MagicMock()
        provider.get_prices.side_effect = ConnectionError("network down")

        with pytest.raises(DataSourceError):
            run(
                strategy=get_strategy("momentum"),
                data_provider=provider,
                ctx=StrategyContext(),
                universe=["AAPL"],
                start_date="2022-01-03",
                end_date="2022-12-30",
            )

    def test_all_missing_symbols_raises_data_not_found(self, mock_data_provider):
        with pytest.raises(DataNotFoundError):
            run(
                strategy=get_strategy("momentum"),
                data_provider=mock_data_provider,
                ctx=StrategyContext(),
                universe=["NOTREAL1", "NOTREAL2"],
                start_date="2022-01-03",
                end_date="2022-12-30",
            )


# ── 리밸런싱 주기 ─────────────────────────────────────────────────────

class TestRebalanceFreq:
    def test_monthly_fewer_trades_than_weekly(self, mock_data_provider):
        # low-vol은 compute_target_weights를 사용하므로 rebalance_freq가 실제로 적용됨
        # trade_log 길이: 월간 ~12, 주간 ~52 → 월간이 반드시 적음
        monthly = run(
            strategy=get_strategy("low-vol"),
            data_provider=mock_data_provider,
            ctx=StrategyContext(params={}),
            universe=["AAPL", "MSFT", "GOOG"],
            start_date="2022-01-03",
            end_date="2022-12-30",
            rebalance_freq="monthly",
        )
        weekly = run(
            strategy=get_strategy("low-vol"),
            data_provider=mock_data_provider,
            ctx=StrategyContext(params={}),
            universe=["AAPL", "MSFT", "GOOG"],
            start_date="2022-01-03",
            end_date="2022-12-30",
            rebalance_freq="weekly",
        )
        assert len(monthly.trade_log) < len(weekly.trade_log)
