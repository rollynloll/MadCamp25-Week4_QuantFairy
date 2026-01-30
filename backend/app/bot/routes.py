from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, BackgroundTasks

from app.core.config import get_settings
from app.core.errors import APIError
from app.core.time import now_kst, plus_hours
from app.schemas.bot import BotRunNowResponse, BotStateResponse
from app.storage.settings_repo import SettingsRepository


router = APIRouter()


def _finalize_run(repo: SettingsRepository, run_id: str) -> None:
    finished_at = now_kst().isoformat()
    last_run = repo.get("bot_last_run", {}) or {}
    started_at = last_run.get("started_at", finished_at)
    repo.set(
        "bot_last_run",
        {
            "run_id": run_id,
            "started_at": started_at,
            "ended_at": finished_at,
            "result": "success",
            "orders_created": last_run.get("orders_created", 0),
            "orders_failed": last_run.get("orders_failed", 0),
        },
    )


def _ensure_not_killed(repo: SettingsRepository) -> None:
    if repo.get("kill_switch", False):
        raise APIError(
            "KILL_SWITCH_ON",
            "Kill switch is enabled",
            "Disable kill switch to run bot",
            status_code=403,
        )


@router.post("/bot/start", response_model=BotStateResponse)
async def start_bot():
    settings = get_settings()
    repo = SettingsRepository(settings)
    repo.set("bot_state", "running")
    repo.set("worker_state", "running")
    repo.set("worker_last_heartbeat_at", now_kst().isoformat())
    return BotStateResponse(state="running")


@router.post("/bot/stop", response_model=BotStateResponse)
async def stop_bot():
    settings = get_settings()
    repo = SettingsRepository(settings)
    repo.set("bot_state", "stopped")
    repo.set("worker_state", "stopped")
    repo.set("worker_last_heartbeat_at", now_kst().isoformat())
    return BotStateResponse(state="stopped")


@router.post("/bot/run-now", response_model=BotRunNowResponse)
async def run_bot_now(background_tasks: BackgroundTasks):
    settings = get_settings()
    repo = SettingsRepository(settings)
    _ensure_not_killed(repo)
    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    started_at = now_kst().isoformat()
    repo.set("bot_state", "running")
    repo.set(
        "bot_last_run",
        {
            "run_id": run_id,
            "started_at": started_at,
            "ended_at": None,
            "result": "partial",
            "orders_created": 0,
            "orders_failed": 0,
        },
    )
    repo.set("next_run_at", plus_hours(1).isoformat())
    background_tasks.add_task(_finalize_run, repo, run_id)
    return BotRunNowResponse(run_id=run_id, state="queued")
