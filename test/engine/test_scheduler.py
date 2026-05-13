"""engine/trading/scheduler.py 테스트 — should_rebalance, run_live."""
from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, call

import pytest

from engine.trading.scheduler import LiveResult, run_live, should_rebalance


# ── should_rebalance ─────────────────────────────────────────────────

class TestShouldRebalance:
    def test_none_last_always_rebalances(self):
        assert should_rebalance("monthly", date(2024, 5, 1), None) is True
        assert should_rebalance("weekly", date(2024, 5, 1), None) is True
        assert should_rebalance("daily", date(2024, 5, 1), None) is True

    # daily
    def test_daily_new_day(self):
        assert should_rebalance("daily", date(2024, 5, 2), date(2024, 5, 1)) is True

    def test_daily_same_day(self):
        assert should_rebalance("daily", date(2024, 5, 1), date(2024, 5, 1)) is False

    # weekly
    def test_weekly_new_week(self):
        # 2024-04-29(월) last, 2024-05-06(월) today → 다른 주
        assert should_rebalance("weekly", date(2024, 5, 6), date(2024, 4, 29)) is True

    def test_weekly_same_week(self):
        # 2024-05-06(월) last, 2024-05-08(수) today → 같은 주
        assert should_rebalance("weekly", date(2024, 5, 8), date(2024, 5, 6)) is False

    def test_weekly_previous_week_boundary(self):
        # 월요일 last, 같은 주 금요일 → 아직 같은 주
        assert should_rebalance("weekly", date(2024, 5, 10), date(2024, 5, 6)) is False

    # monthly
    def test_monthly_new_month(self):
        assert should_rebalance("monthly", date(2024, 6, 3), date(2024, 5, 31)) is True

    def test_monthly_same_month(self):
        assert should_rebalance("monthly", date(2024, 5, 15), date(2024, 5, 1)) is False

    def test_monthly_year_boundary(self):
        assert should_rebalance("monthly", date(2025, 1, 2), date(2024, 12, 31)) is True


# ── run_live ─────────────────────────────────────────────────────────

class TestRunLive:
    def test_skips_when_not_rebalance_day(self, mock_broker, mock_data_provider, ctx):
        from engine.strategies.registry import get_strategy
        strategy = get_strategy("momentum")
        result = run_live(
            strategy=strategy,
            data_provider=mock_data_provider,
            broker=mock_broker,
            ctx=ctx,
            universe=["AAPL", "MSFT"],
            rebalance_freq="monthly",
            last_rebalance_date=date.today(),  # 오늘 이미 실행
            dry_run=True,
        )
        assert result.did_rebalance is False
        assert result.orders == []
        assert "리밸런싱 주기" in (result.skipped_reason or "")
        mock_broker.place_orders.assert_not_called()

    def test_dry_run_does_not_place_orders(self, mock_broker, mock_data_provider, ctx):
        strategy = MagicMock()
        strategy.compute_target_weights.return_value = {"AAPL": 0.5, "MSFT": 0.5}

        result = run_live(
            strategy=strategy,
            data_provider=mock_data_provider,
            broker=mock_broker,
            ctx=ctx,
            universe=["AAPL", "MSFT"],
            rebalance_freq="monthly",
            last_rebalance_date=None,
            dry_run=True,
        )
        assert result.did_rebalance is True
        mock_broker.place_orders.assert_not_called()

    def test_execute_places_orders(self, mock_broker, mock_data_provider, ctx):
        strategy = MagicMock()
        strategy.compute_target_weights.return_value = {"AAPL": 0.6, "MSFT": 0.4}

        run_live(
            strategy=strategy,
            data_provider=mock_data_provider,
            broker=mock_broker,
            ctx=ctx,
            universe=["AAPL", "MSFT"],
            rebalance_freq="monthly",
            last_rebalance_date=None,
            dry_run=False,
        )
        mock_broker.place_orders.assert_called_once()

    def test_capital_pct_scales_order_notional(self, mock_data_provider, ctx):
        """capital_pct=0.4이면 $100k 계좌에서 $40k 기준으로 주문을 산정한다."""
        from engine.trading.account import Account

        broker = MagicMock()
        broker.get_account.return_value = Account(
            equity=100_000.0, cash=100_000.0, buying_power=100_000.0, portfolio_value=0.0
        )
        broker.get_positions.return_value = []
        broker.place_orders.return_value = ["o1"]

        strategy = MagicMock()
        strategy.compute_target_weights.return_value = {"AAPL": 1.0}  # 전체 배분

        result = run_live(
            strategy=strategy,
            data_provider=mock_data_provider,
            broker=broker,
            ctx=ctx,
            universe=["AAPL"],
            rebalance_freq="monthly",
            last_rebalance_date=None,
            capital_pct=0.4,
            dry_run=True,
        )
        assert result.did_rebalance is True
        assert len(result.orders) == 1
        # 전체 $100k × 0.4 = $40k 기준 → AAPL 100% → 매수 $40k
        assert result.orders[0].notional == pytest.approx(40_000.0)

    def test_result_contains_equity(self, mock_broker, mock_data_provider, ctx):
        strategy = MagicMock()
        strategy.compute_target_weights.return_value = {"AAPL": 0.5}

        result = run_live(
            strategy=strategy,
            data_provider=mock_data_provider,
            broker=mock_broker,
            ctx=ctx,
            universe=["AAPL"],
            rebalance_freq="monthly",
            last_rebalance_date=None,
            dry_run=True,
        )
        assert result.equity == pytest.approx(100_000.0)

    def test_result_contains_current_positions(
        self, mock_broker, mock_data_provider, ctx, positions_with_holdings
    ):
        mock_broker.get_positions.return_value = positions_with_holdings
        strategy = MagicMock()
        strategy.compute_target_weights.return_value = {}

        result = run_live(
            strategy=strategy,
            data_provider=mock_data_provider,
            broker=mock_broker,
            ctx=ctx,
            universe=["AAPL", "MSFT"],
            rebalance_freq="monthly",
            last_rebalance_date=None,
            dry_run=True,
        )
        assert len(result.current_positions) == 2

    def test_orders_sells_before_buys(self, mock_data_provider, ctx):
        """run_live 결과의 주문도 sell이 buy보다 앞에 있어야 한다."""
        from engine.trading.account import Account
        from engine.trading.position import Position

        broker = MagicMock()
        broker.get_account.return_value = Account(
            equity=10_000.0, cash=5_000.0, buying_power=5_000.0, portfolio_value=5_000.0
        )
        broker.get_positions.return_value = [
            Position(symbol="AAPL", qty=50.0, market_value=5_000.0)
        ]
        broker.place_orders.return_value = []

        strategy = MagicMock()
        strategy.compute_target_weights.return_value = {"MSFT": 0.5}  # AAPL 청산 → MSFT 매수

        result = run_live(
            strategy=strategy,
            data_provider=mock_data_provider,
            broker=broker,
            ctx=ctx,
            universe=["AAPL", "MSFT"],
            rebalance_freq="monthly",
            last_rebalance_date=None,
            dry_run=True,
        )
        if len(result.orders) >= 2:
            sell_idx = next(i for i, o in enumerate(result.orders) if o.side == "sell")
            buy_idx = next(i for i, o in enumerate(result.orders) if o.side == "buy")
            assert sell_idx < buy_idx
