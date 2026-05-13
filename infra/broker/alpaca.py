from __future__ import annotations

import os
from typing import List

from engine.trading.account import Account
from engine.trading.order import Order
from engine.trading.position import Position


class AlpacaBroker:
    """Alpaca Trading API 브로커 어댑터.

    환경 변수:
        ALPACA_API_KEY    : Alpaca API 키
        ALPACA_SECRET_KEY : Alpaca Secret 키
        ALPACA_PAPER      : "true"이면 페이퍼 트레이딩 (기본값 "true")
    """

    def __init__(self) -> None:
        from alpaca.trading.client import TradingClient

        api_key = os.environ["ALPACA_API_KEY_ID"]
        secret_key = os.environ["ALPACA_API_SECRET_KEY"]
        # ALPACA_MODE=live → live, 그 외 → paper (기본값)
        mode = os.environ.get("ALPACA_MODE", "paper").lower()
        paper = mode != "live"
        self._client = TradingClient(api_key, secret_key, paper=paper)

    def get_account(self) -> Account:
        a = self._client.get_account()
        equity = float(a.equity)
        cash = float(a.cash)
        return Account(
            equity=equity,
            cash=cash,
            buying_power=float(a.buying_power),
            portfolio_value=float(a.portfolio_value),
            currency=str(a.currency) if hasattr(a, "currency") else "USD",
        )

    def get_positions(self) -> List[Position]:
        raw = self._client.get_all_positions()
        return [
            Position(
                symbol=p.symbol,
                qty=float(p.qty),
                market_value=float(p.market_value),
                avg_entry_price=float(p.avg_entry_price),
                unrealized_pnl=float(p.unrealized_pl),
                unrealized_pnl_pct=float(p.unrealized_plpc),
            )
            for p in raw
        ]

    def place_orders(self, orders: List[Order]) -> List[str]:
        from alpaca.trading.enums import OrderSide, TimeInForce
        from alpaca.trading.requests import MarketOrderRequest

        order_ids: List[str] = []
        for order in orders:
            side = OrderSide.BUY if order.side == "buy" else OrderSide.SELL
            req = MarketOrderRequest(
                symbol=order.symbol,
                notional=round(order.notional, 2),
                side=side,
                time_in_force=TimeInForce.DAY,
            )
            result = self._client.submit_order(req)
            order_ids.append(str(result.id))
        return order_ids

    def is_market_open(self) -> bool:
        clock = self._client.get_clock()
        return bool(clock.is_open)

    def cancel_all_orders(self) -> None:
        self._client.cancel_orders()
