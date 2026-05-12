from __future__ import annotations

from typing import Dict, List

from engine.trading.order import Order
from engine.trading.position import Position


def compute_orders(
    target_weights: Dict[str, float],
    current_positions: List[Position],
    equity: float,
    min_order_notional: float = 1.0,
) -> List[Order]:
    """(목표 비중, 현재 포지션, 총 자산) → 실행할 주문 목록.

    순수 함수. 인프라 의존 없음 — 백테스트 엔진처럼 단독 테스트 가능.

    처리 규칙:
      - 목표 비중이 0이거나 target_weights에 없는 보유 종목 → 전량 매도
      - 목표 금액 > 현재 금액 + min_order_notional → 차액만큼 매수
      - 목표 금액 < 현재 금액 - min_order_notional → 차액만큼 매도
      - |차액| ≤ min_order_notional → 주문 생략 (소액 리밸런싱 방지)
    """
    current: Dict[str, float] = {p.symbol: p.market_value for p in current_positions}
    orders: List[Order] = []

    # 보유 중이지만 목표 비중이 없는 종목 → 전량 청산
    for symbol, value in current.items():
        if symbol not in target_weights and value > min_order_notional:
            orders.append(Order(symbol=symbol, side="sell", notional=value))

    # 목표 비중 대비 차액 매수·매도
    for symbol, weight in target_weights.items():
        target_value = weight * equity
        current_value = current.get(symbol, 0.0)
        delta = target_value - current_value
        if delta > min_order_notional:
            orders.append(Order(symbol=symbol, side="buy", notional=delta))
        elif delta < -min_order_notional:
            orders.append(Order(symbol=symbol, side="sell", notional=abs(delta)))

    return orders
