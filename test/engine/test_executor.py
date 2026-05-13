"""engine/trading/executor.py 테스트 — compute_orders 핵심 로직."""
from __future__ import annotations

import pytest

from engine.trading.executor import compute_orders
from engine.trading.order import Order
from engine.trading.position import Position


def _pos(symbol: str, value: float) -> Position:
    return Position(symbol=symbol, qty=1.0, market_value=value)


# ── 기본 케이스 ──────────────────────────────────────────────────────

class TestComputeOrdersBasic:
    def test_no_positions_no_target_returns_empty(self):
        orders = compute_orders({}, [], equity=100_000.0)
        assert orders == []

    def test_buy_only_no_current_positions(self):
        target = {"AAPL": 0.5, "MSFT": 0.3}
        orders = compute_orders(target, [], equity=10_000.0)
        assert len(orders) == 2
        assert all(o.side == "buy" for o in orders)
        symbols = {o.symbol for o in orders}
        assert symbols == {"AAPL", "MSFT"}

    def test_sell_only_position_not_in_target(self):
        positions = [_pos("AAPL", 5_000.0)]
        orders = compute_orders({}, positions, equity=10_000.0)
        assert len(orders) == 1
        assert orders[0].side == "sell"
        assert orders[0].symbol == "AAPL"
        assert orders[0].notional == pytest.approx(5_000.0)

    def test_buy_and_sell_both_present(self):
        positions = [_pos("AAPL", 4_000.0)]
        target = {"MSFT": 0.5}  # AAPL → 청산, MSFT → 매수
        orders = compute_orders(target, positions, equity=10_000.0)
        sides = {o.side for o in orders}
        assert "buy" in sides
        assert "sell" in sides

    def test_increase_position_produces_buy(self):
        positions = [_pos("AAPL", 2_000.0)]
        target = {"AAPL": 0.5}   # 목표 $5,000 > 현재 $2,000 → 매수 $3,000
        orders = compute_orders(target, positions, equity=10_000.0)
        assert len(orders) == 1
        assert orders[0].side == "buy"
        assert orders[0].notional == pytest.approx(3_000.0)

    def test_decrease_position_produces_sell(self):
        positions = [_pos("AAPL", 8_000.0)]
        target = {"AAPL": 0.5}   # 목표 $5,000 < 현재 $8,000 → 매도 $3,000
        orders = compute_orders(target, positions, equity=10_000.0)
        assert len(orders) == 1
        assert orders[0].side == "sell"
        assert orders[0].notional == pytest.approx(3_000.0)


# ── Sell 먼저 / Buy 나중 순서 ────────────────────────────────────────

class TestSellFirstOrdering:
    def test_sells_come_before_buys(self):
        """매도 주문이 반드시 매수 주문보다 앞에 와야 한다."""
        positions = [
            _pos("AAPL", 5_000.0),   # 목표 없음 → 전량 매도
            _pos("MSFT", 3_000.0),   # 목표 $2,000 → $1,000 매도
        ]
        target = {
            "MSFT": 0.2,   # $2,000
            "GOOG": 0.3,   # $3,000 매수
        }
        orders = compute_orders(target, positions, equity=10_000.0)

        # 매도가 먼저, 매수가 나중
        sell_indices = [i for i, o in enumerate(orders) if o.side == "sell"]
        buy_indices = [i for i, o in enumerate(orders) if o.side == "buy"]
        assert sell_indices, "매도 주문이 없음"
        assert buy_indices, "매수 주문이 없음"
        assert max(sell_indices) < min(buy_indices), (
            f"매도(idx={sell_indices})가 매수(idx={buy_indices})보다 뒤에 있음"
        )

    def test_all_sells_then_all_buys(self):
        """여러 매도와 여러 매수가 섞인 경우에도 순서 보장."""
        positions = [_pos(sym, 2_000.0) for sym in ["A", "B", "C"]]
        target = {"D": 0.2, "E": 0.2, "F": 0.2}  # 기존 3개 매도, 신규 3개 매수
        orders = compute_orders(target, positions, equity=10_000.0)
        first_buy_idx = next(i for i, o in enumerate(orders) if o.side == "buy")
        for i in range(first_buy_idx):
            assert orders[i].side == "sell"

    def test_only_sells_no_buys(self):
        positions = [_pos("AAPL", 5_000.0), _pos("MSFT", 3_000.0)]
        orders = compute_orders({}, positions, equity=10_000.0)
        assert all(o.side == "sell" for o in orders)

    def test_only_buys_no_sells(self):
        target = {"AAPL": 0.4, "MSFT": 0.3}
        orders = compute_orders(target, [], equity=10_000.0)
        assert all(o.side == "buy" for o in orders)


# ── min_order_notional 임계값 ────────────────────────────────────────

class TestMinNotional:
    def test_small_delta_ignored(self):
        positions = [_pos("AAPL", 5_000.5)]
        target = {"AAPL": 0.5}   # 목표 $5,000, 현재 $5,000.5 → delta=$0.5
        orders = compute_orders(target, positions, equity=10_000.0, min_order_notional=1.0)
        assert orders == []

    def test_delta_above_threshold_generates_order(self):
        positions = [_pos("AAPL", 4_990.0)]
        target = {"AAPL": 0.5}   # 목표 $5,000, delta=$10 > $1 threshold
        orders = compute_orders(target, positions, equity=10_000.0, min_order_notional=1.0)
        assert len(orders) == 1

    def test_small_position_not_liquidated(self):
        positions = [_pos("AAPL", 0.5)]  # $0.50 — min_order=1.0 미만
        orders = compute_orders({}, positions, equity=10_000.0, min_order_notional=1.0)
        assert orders == []

    def test_large_position_liquidated(self):
        positions = [_pos("AAPL", 100.0)]
        orders = compute_orders({}, positions, equity=10_000.0, min_order_notional=1.0)
        assert len(orders) == 1
        assert orders[0].side == "sell"

    def test_zero_threshold_catches_tiny_delta(self):
        positions = [_pos("AAPL", 5_000.01)]
        target = {"AAPL": 0.5}
        orders = compute_orders(target, positions, equity=10_000.0, min_order_notional=0.0)
        assert len(orders) == 1


# ── 엣지 케이스 ─────────────────────────────────────────────────────

class TestEdgeCases:
    def test_zero_equity_no_crash(self):
        orders = compute_orders({"AAPL": 0.5}, [], equity=0.0)
        # target_value = 0 → delta ≤ 0 → no buy
        assert all(o.side != "buy" for o in orders)

    def test_target_weight_zero_liquidates_position(self):
        positions = [_pos("AAPL", 5_000.0)]
        target = {"AAPL": 0.0}
        # weight=0 → target_value=0 → delta=-5000 → sell
        orders = compute_orders(target, positions, equity=10_000.0)
        sells = [o for o in orders if o.side == "sell" and o.symbol == "AAPL"]
        assert len(sells) == 1

    def test_weights_over_100pct_proportional(self):
        # 비중 합계 > 1.0 이어도 계산은 그대로 진행
        target = {"AAPL": 0.6, "MSFT": 0.6}
        orders = compute_orders(target, [], equity=10_000.0)
        assert all(o.side == "buy" for o in orders)
        total_notional = sum(o.notional for o in orders)
        assert total_notional == pytest.approx(12_000.0)

    def test_notional_values_correct(self):
        target = {"AAPL": 0.4, "MSFT": 0.3}
        orders = compute_orders(target, [], equity=10_000.0)
        order_map = {o.symbol: o.notional for o in orders}
        assert order_map["AAPL"] == pytest.approx(4_000.0)
        assert order_map["MSFT"] == pytest.approx(3_000.0)

    def test_position_already_at_target_no_order(self):
        positions = [_pos("AAPL", 5_000.0)]
        target = {"AAPL": 0.5}
        orders = compute_orders(target, positions, equity=10_000.0)
        assert orders == []

    def test_multiple_positions_partial_change(self):
        positions = [_pos("AAPL", 3_000.0), _pos("MSFT", 3_000.0)]
        target = {"AAPL": 0.5}  # AAPL 증가, MSFT 청산
        orders = compute_orders(target, positions, equity=10_000.0)
        sells = [o for o in orders if o.side == "sell"]
        buys = [o for o in orders if o.side == "buy"]
        assert any(o.symbol == "MSFT" for o in sells)
        assert any(o.symbol == "AAPL" for o in buys)
