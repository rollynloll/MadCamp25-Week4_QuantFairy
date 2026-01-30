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
