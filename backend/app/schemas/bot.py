from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class BotStateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: Literal["running", "stopped", "error"]


class BotRunNowResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    state: Literal["queued"]
