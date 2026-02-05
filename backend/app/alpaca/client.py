from __future__ import annotations

import time
from dataclasses import dataclass

from app.core.config import Settings
import logging

try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import GetPortfolioHistoryRequest
    from alpaca.trading.requests import GetOrdersRequest
    from alpaca.trading.requests import MarketOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce
except Exception:  # pragma: no cover - optional dependency
    TradingClient = None
    GetPortfolioHistoryRequest = None
    GetOrdersRequest = None
    MarketOrderRequest = None
    OrderSide = None
    TimeInForce = None


LIVE_BASE_URL = "https://api.alpaca.markets"
logger = logging.getLogger("uvicorn.error")


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
            logger.warning("alpaca.client not configured (missing keys)")
            return None
        if TradingClient is None:
            logger.error("alpaca.client dependency not available (alpaca-py)")
            return None
        if self._client is None:
            try:
                logger.info(
                    "alpaca.client init env=%s base_url=%s",
                    self.environment,
                    self.settings.alpaca_base_url if self.environment == "paper" else LIVE_BASE_URL,
                )
                self._client = TradingClient(
                    self.settings.alpaca_api_key,
                    self.settings.alpaca_secret_key,
                    paper=self.environment == "paper",
                    base_url=self.settings.alpaca_base_url
                    if self.environment == "paper"
                    else LIVE_BASE_URL,
                )
            except TypeError:
                logger.info(
                    "alpaca.client init fallback env=%s (no base_url param)",
                    self.environment,
                )
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
            logger.info("alpaca.get_account ok latency_ms=%s", latency_ms)
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
            logger.error("alpaca.get_account failed latency_ms=%s error=%s", latency_ms, exc)
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
                result = client.get_portfolio_history(request)
                logger.info("alpaca.get_portfolio_history ok period=%s timeframe=%s", period, timeframe)
                return result
            if period or timeframe:
                result = client.get_portfolio_history(period=period, timeframe=timeframe)
                logger.info("alpaca.get_portfolio_history ok period=%s timeframe=%s", period, timeframe)
                return result
            result = client.get_portfolio_history()
            logger.info("alpaca.get_portfolio_history ok period=%s timeframe=%s", period, timeframe)
            return result
        except Exception:
            logger.error("alpaca.get_portfolio_history failed period=%s timeframe=%s", period, timeframe)
            return None

    def get_positions(self):
        client = self._get_client()
        if client is None:
            return None
        try:  # pragma: no cover - depends on Alpaca
            result = client.get_all_positions()
            logger.info("alpaca.get_positions ok count=%s", len(result) if result is not None else 0)
            return result
        except Exception as exc:
            logger.error("alpaca.get_positions failed error=%s", exc)
            return None

    def get_orders(self, status: str | None = None, limit: int | None = None):
        client = self._get_client()
        if client is None:
            return None
        try:  # pragma: no cover - depends on Alpaca
            if GetOrdersRequest is not None:
                payload = {}
                if status:
                    payload["status"] = status
                if limit:
                    payload["limit"] = limit
                request = GetOrdersRequest(**payload)
                result = client.get_orders(request)
            else:
                kwargs = {}
                if status:
                    kwargs["status"] = status
                if limit:
                    kwargs["limit"] = limit
                result = client.get_orders(**kwargs)
            logger.info(
                "alpaca.get_orders ok count=%s status=%s",
                len(result) if result is not None else 0,
                status,
            )
            return result
        except Exception as exc:
            logger.error("alpaca.get_orders failed status=%s error=%s", status, exc)
            return None

    def is_market_open(self) -> bool | None:
        client = self._get_client()
        if client is None:
            return None
        try:  # pragma: no cover - depends on Alpaca
            clock = client.get_clock()
            is_open = bool(getattr(clock, "is_open", False))
            logger.info("alpaca.get_clock ok is_open=%s", is_open)
            return is_open
        except Exception as exc:
            logger.error("alpaca.get_clock failed error=%s", exc)
            return None

    def cancel_open_orders(self, limit: int = 500) -> dict:
        """Cancel currently open Alpaca orders, used before after-hours rebalance reruns."""
        client = self._get_client()
        if client is None:
            return {"requested": 0, "canceled": 0, "failed": 0, "canceled_ids": [], "failed_ids": []}
        try:  # pragma: no cover - depends on Alpaca
            all_orders = self.get_orders(status="all", limit=limit) or []
            final_statuses = {"filled", "canceled", "cancelled", "rejected", "expired"}
            open_orders = []
            for order in all_orders:
                status = getattr(order, "status", None)
                status_text = str(status or "").strip().lower()
                if "." in status_text:
                    status_text = status_text.split(".")[-1]
                if status_text in final_statuses:
                    continue
                open_orders.append(order)
            canceled_ids: list[str] = []
            failed_ids: list[str] = []
            for order in open_orders:
                order_id = getattr(order, "id", None) or getattr(order, "client_order_id", None)
                if not order_id:
                    continue
                try:
                    client.cancel_order_by_id(str(order_id))
                    canceled_ids.append(str(order_id))
                except Exception:
                    failed_ids.append(str(order_id))
            logger.info(
                "alpaca.cancel_open_orders requested=%s canceled=%s failed=%s",
                len(open_orders),
                len(canceled_ids),
                len(failed_ids),
            )
            return {
                "requested": len(all_orders),
                "open_detected": len(open_orders),
                "canceled": len(canceled_ids),
                "failed": len(failed_ids),
                "canceled_ids": canceled_ids,
                "failed_ids": failed_ids,
            }
        except Exception as exc:
            logger.error("alpaca.cancel_open_orders failed error=%s", exc)
            return {
                "requested": 0,
                "open_detected": 0,
                "canceled": 0,
                "failed": 0,
                "canceled_ids": [],
                "failed_ids": [],
            }

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
            logger.error("alpaca.submit_order failed: client not configured")
            return {"ok": False, "error": "Alpaca client not configured", "order": None}
        if qty is None and notional is None:
            logger.error("alpaca.submit_order failed: qty or notional required")
            return {"ok": False, "error": "qty or notional required", "order": None}
        if qty is not None and notional is not None:
            logger.error("alpaca.submit_order failed: qty and notional are mutually exclusive")
            return {"ok": False, "error": "qty and notional are mutually exclusive", "order": None}
        try:  # pragma: no cover - depends on Alpaca
            order = MarketOrderRequest(
                symbol=symbol,
                side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
                qty=qty,
                notional=notional,
                time_in_force=TimeInForce(time_in_force),
            )
            result = client.submit_order(order)
            logger.info("alpaca.submit_order ok symbol=%s side=%s qty=%s notional=%s", symbol, side, qty, notional)
            return {"ok": True, "error": None, "order": result}
        except Exception as exc:
            logger.error("alpaca.submit_order failed symbol=%s side=%s error=%s", symbol, side, exc)
            return {"ok": False, "error": str(exc), "order": None}
