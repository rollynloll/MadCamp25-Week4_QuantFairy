from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List

import pandas as pd

from engine.data.protocol import DataProvider
from engine.strategies.base import Strategy, StrategyContext
from engine.trading.broker import BrokerProvider
from engine.trading.executor import compute_orders
from engine.trading.order import Order
from engine.trading.position import Position


@dataclass
class LiveResult:
    date: str                           # 실행 날짜 (YYYY-MM-DD)
    did_rebalance: bool                 # 실제로 리밸런싱이 발생했는지 여부
    equity: float                       # 실행 시점 총 자산
    target_weights: Dict[str, float]    # 전략이 계산한 목표 비중
    current_positions: List[Position]   # 실행 전 보유 포지션
    orders: List[Order]                 # 생성된 주문 목록 (dry_run=True이면 실행 안 됨)
    skipped_reason: str | None = field(default=None)  # 리밸런싱 건너뛴 이유


def should_rebalance(freq: str, today: date, last_rebalance: date | None) -> bool:
    """오늘이 리밸런싱 날인지 판단한다. last_rebalance가 None이면 항상 True."""
    if last_rebalance is None:
        return True
    if freq == "daily":
        return today > last_rebalance
    if freq == "weekly":
        return today.isocalendar().week != last_rebalance.isocalendar().week
    if freq == "monthly":
        return (today.year, today.month) != (last_rebalance.year, last_rebalance.month)
    return False


def run_live(
    *,
    strategy: Strategy,
    data_provider: DataProvider,
    broker: BrokerProvider,
    ctx: StrategyContext,
    universe: List[str],
    rebalance_freq: str = "monthly",
    lookback_days: int = 400,       # 전략 룩백 + 여유분 (모멘텀 기본 252일 → 400일)
    last_rebalance_date: date | None = None,
    capital_pct: float = 1.0,       # 전체 자산 중 이 봇에 배분된 비율 (기본 100%)
    min_order_notional: float = 1.0,
    dry_run: bool = True,           # True면 주문 계산만 하고 실제 실행은 하지 않음
) -> LiveResult:
    """자동매매 한 사이클을 실행한다.

    흐름:
      1. 리밸런싱 날짜 여부 확인
      2. 가격 데이터 조회 (lookback_days)
      3. 전략으로 목표 비중 계산
      4. 브로커에서 현재 포지션·자산 조회
      5. compute_orders()로 주문 목록 생성
      6. dry_run=False이면 broker.place_orders() 실행

    dry_run=True (기본값)이면 주문을 실제로 제출하지 않는다.
    리밸런싱 날이 아니면 orders=[]로 즉시 반환한다.
    """
    today = date.today()

    # 리밸런싱 날이 아니면 조기 반환
    if not should_rebalance(rebalance_freq, today, last_rebalance_date):
        positions = broker.get_positions()
        equity = broker.get_account().equity
        current_weights = (
            {p.symbol: p.market_value / equity for p in positions} if equity else {}
        )
        return LiveResult(
            date=str(today),
            did_rebalance=False,
            equity=equity,
            target_weights=current_weights,
            current_positions=positions,
            orders=[],
            skipped_reason=f"리밸런싱 주기({rebalance_freq}) 미도달",
        )

    # 가격 데이터 조회
    start = (today - timedelta(days=lookback_days)).isoformat()
    end = today.isoformat()
    prices_wide = data_provider.get_prices(universe, start, end)
    prices_df = (
        prices_wide.stack()
        .to_frame("adj_close")
        .rename_axis(["date", "symbol"])
    )

    # 목표 비중 계산 — compute_target_weights 우선, NotImplementedError면 generate_signals 폴백
    dt = pd.Timestamp(today)
    try:
        target_weights = strategy.compute_target_weights(prices_df, ctx, universe, dt)
    except NotImplementedError:
        # generate_signals는 전체 기간 신호를 생성하므로 마지막 신호를 사용한다
        signals = list(strategy.generate_signals(prices_df, ctx, universe))
        target_weights = signals[-1].target_weights if signals else {}

    # 브로커에서 현재 상태 조회
    positions = broker.get_positions()
    equity = broker.get_account().equity

    # 주문 생성 (capital_pct만큼의 자산만 사용)
    orders = compute_orders(target_weights, positions, equity * capital_pct, min_order_notional)

    # 실제 주문 실행 (dry_run=False일 때만)
    if not dry_run and orders:
        broker.place_orders(orders)

    return LiveResult(
        date=str(today),
        did_rebalance=True,
        equity=equity,
        target_weights=target_weights,
        current_positions=positions,
        orders=orders,
    )
