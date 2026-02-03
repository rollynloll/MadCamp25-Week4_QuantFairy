from __future__ import annotations

import time
from dataclasses import dataclass

from app.core.config import Settings

try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import GetPortfolioHistoryRequest
    from alpaca.trading.requests import MarketOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce
except Exception:  # pragma: no cover - optional dependency
    TradingClient = None
    GetPortfolioHistoryRequest = None
    MarketOrderRequest = None
    OrderSide = None
    TimeInForce = None


LIVE_BASE_URL = "https://api.alpaca.markets"


@dataclass
class AlpacaAccount:
    equity: float
    cash: float
    buying_power: float
    currency: str


@dataclass
class AlpacaAccountResult:
    account: AlpacaAccount | None
    latency_ms: int | None
    error: str | None = None


class AlpacaClient:
    def __init__(self, settings: Settings, environment: str) -> None:
        self.settings = settings
        self.environment = environment
        self._client = None

    def _configured(self) -> bool:
        return bool(self.settings.alpaca_api_key and self.settings.alpaca_secret_key)

    def _get_client(self):
        if not self._configured():
            return None
        if TradingClient is None:
            return None
        if self._client is None:
            try:
                self._client = TradingClient(
                    self.settings.alpaca_api_key,
                    self.settings.alpaca_secret_key,
                    paper=self.environment == "paper",
                    base_url=self.settings.alpaca_base_url
                    if self.environment == "paper"
                    else LIVE_BASE_URL,
                )
            except TypeError:
                self._client = TradingClient(
                    self.settings.alpaca_api_key,
                    self.settings.alpaca_secret_key,
                    paper=self.environment == "paper",
                )
        return self._client

    def get_account(self) -> AlpacaAccountResult:
        client = self._get_client()
        if client is None:
            return AlpacaAccountResult(
                account=None,
                latency_ms=None,
                error="Alpaca client not configured",
            )
        start = time.monotonic()
        try:
            account = client.get_account()
            latency_ms = int((time.monotonic() - start) * 1000)
            return AlpacaAccountResult(
                account=AlpacaAccount(
                    equity=float(account.equity),
                    cash=float(account.cash),
                    buying_power=float(account.buying_power),
                    currency=str(account.currency),
                ),
                latency_ms=latency_ms,
            )
        except Exception as exc:  # pragma: no cover - depends on Alpaca
            latency_ms = int((time.monotonic() - start) * 1000)
            return AlpacaAccountResult(
                account=None, latency_ms=latency_ms, error=str(exc)
            )

    def get_portfolio_history(
        self,
        period: str | None = None,
        timeframe: str | None = None,
    ):
        client = self._get_client()
        if client is None:
            return None
        try:  # pragma: no cover - depends on Alpaca
            if GetPortfolioHistoryRequest is not None:
                payload = {}
                if period:
                    payload["period"] = period
                if timeframe:
                    payload["timeframe"] = timeframe
                request = GetPortfolioHistoryRequest(**payload)
                return client.get_portfolio_history(request)
            if period or timeframe:
                return client.get_portfolio_history(period=period, timeframe=timeframe)
            return client.get_portfolio_history()
        except Exception:
            return None

    def get_positions(self):
        client = self._get_client()
        if client is None:
            return None
        try:  # pragma: no cover - depends on Alpaca
            return client.get_all_positions()
        except Exception:
            return None

    def submit_market_order(
        self,
        *,
        symbol: str,
        side: str,
        qty: float | None = None,
        notional: float | None = None,
        time_in_force: str = "day",
    ):
        client = self._get_client()
        if client is None or MarketOrderRequest is None or OrderSide is None or TimeInForce is None:
            return None
        if qty is None and notional is None:
            return None
        if qty is not None and notional is not None:
            return None
        try:  # pragma: no cover - depends on Alpaca
            order = MarketOrderRequest(
                symbol=symbol,
                side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
                qty=qty,
                notional=notional,
                time_in_force=TimeInForce(time_in_force),
            )
            return client.submit_order(order)
        except Exception:
            return None
