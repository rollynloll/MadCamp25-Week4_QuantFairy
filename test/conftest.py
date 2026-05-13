"""공통 픽스처 모음."""
from __future__ import annotations

from datetime import date
from typing import Dict, List
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from engine.strategies.base import StrategyContext, StrategySignal
from engine.trading.account import Account
from engine.trading.order import Order
from engine.trading.position import Position


# ── 자산 곡선 픽스처 ────────────────────────────────────────────────

@pytest.fixture
def rising_curve() -> List[Dict]:
    """$10,000 → $11,000 (10% 수익, 11일)."""
    return [{"date": f"2024-01-{i+1:02d}", "equity": 10_000 + i * 100} for i in range(11)]


@pytest.fixture
def flat_curve() -> List[Dict]:
    """변동 없는 자산 곡선 (수익률 0)."""
    return [{"date": f"2024-01-{i+1:02d}", "equity": 10_000.0} for i in range(10)]


@pytest.fixture
def declining_curve() -> List[Dict]:
    """$10,000 → $5,000 (50% 손실, 11일)."""
    return [{"date": f"2024-01-{i+1:02d}", "equity": 10_000 - i * 500} for i in range(11)]


@pytest.fixture
def recovery_curve() -> List[Dict]:
    """하락 후 회복: 10000 → 8000 → 10000."""
    pts = [10_000, 9_000, 8_000, 8_500, 9_000, 9_500, 10_000]
    return [{"date": f"2024-01-{i+1:02d}", "equity": e} for i, e in enumerate(pts)]


# ── 가격 데이터 픽스처 ───────────────────────────────────────────────

@pytest.fixture
def sample_prices() -> pd.DataFrame:
    """3종목 2년치 일별 종가 (wide format, deterministic)."""
    dates = pd.date_range("2022-01-03", "2023-12-29", freq="B")
    rng = np.random.default_rng(42)
    data = {}
    for ticker in ["AAPL", "MSFT", "GOOG"]:
        rets = rng.normal(0.0005, 0.015, size=len(dates))
        data[ticker] = 100.0 * np.cumprod(1 + rets)
    return pd.DataFrame(data, index=dates)


@pytest.fixture
def mock_data_provider(sample_prices):
    """임의의 티커 요청에 sample_prices를 슬라이싱해서 반환하는 DataProvider 목."""
    provider = MagicMock()

    def _get_prices(tickers, start, end):
        cols = [t for t in tickers if t in sample_prices.columns]
        if not cols:
            return pd.DataFrame()
        mask = (sample_prices.index >= start) & (sample_prices.index <= end)
        return sample_prices.loc[mask, cols]

    provider.get_prices.side_effect = _get_prices
    return provider


# ── 브로커 / 포지션 픽스처 ──────────────────────────────────────────

@pytest.fixture
def empty_account() -> Account:
    return Account(equity=100_000.0, cash=100_000.0, buying_power=100_000.0, portfolio_value=0.0)


@pytest.fixture
def mock_broker(empty_account):
    """포지션 없는 기본 브로커 목."""
    broker = MagicMock()
    broker.get_account.return_value = empty_account
    broker.get_positions.return_value = []
    broker.place_orders.return_value = ["order-id-1"]
    broker.is_market_open.return_value = True
    broker.cancel_all_orders.return_value = None
    return broker


@pytest.fixture
def positions_with_holdings():
    """AAPL $40k + MSFT $30k 보유 포지션."""
    return [
        Position(symbol="AAPL", qty=300.0, market_value=40_000.0, avg_entry_price=120.0),
        Position(symbol="MSFT", qty=120.0, market_value=30_000.0, avg_entry_price=230.0),
    ]


# ── 전략 픽스처 ─────────────────────────────────────────────────────

@pytest.fixture
def equal_weight_strategy():
    """상위 2종목에 균등 배분하는 전략 목."""
    strat = MagicMock()
    strat.name = "equal_weight_test"

    def _compute(prices, ctx, universe, dt):
        top = universe[:2]
        return {s: 0.5 for s in top}

    strat.compute_target_weights.side_effect = _compute
    return strat


@pytest.fixture
def ctx() -> StrategyContext:
    return StrategyContext(params={})
