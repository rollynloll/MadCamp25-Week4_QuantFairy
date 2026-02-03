from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class TradingModeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    environment: Literal["paper", "live"]


class TradingModeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    environment: Literal["paper", "live"]


class KillSwitchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool
    reason: str | None = None


class KillSwitchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool


class OrderItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: str
    submitted_at: str | None
    symbol: str | None
    side: str | None
    type: str | None
    qty: float
    status: str | None
    filled_at: str | None
    strategy_id: str | None


class OrderListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[OrderItem]


class OrderDetailResponse(OrderItem):
    model_config = ConfigDict(extra="forbid")


class PositionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str | None
    qty: float
    avg_price: float
    unrealized_pnl: float
    strategy_id: str | None
    updated_at: str | None


class PositionListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[PositionItem]


class LastFillResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    price: float
    filled_at: str | None


class BarItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    time: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class BarsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    timeframe: str
    feed: str | None
    bars: list[BarItem]
