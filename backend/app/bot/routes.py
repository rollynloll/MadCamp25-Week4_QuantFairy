from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Header, Query

from app.core.config import get_settings
from app.core.errors import APIError
from app.core.user import resolve_user_id
from app.core.time import plus_hours
from app.schemas.bot import BotRunNowResponse, BotStateResponse
from app.storage.bot_runs_repo import BotRunsRepository
from app.storage.user_settings_repo import UserSettingsRepository


router = APIRouter()


def _finalize_run(repo: BotRunsRepository, run_id: str) -> None:
    repo.finalize_run(run_id)


def _ensure_not_killed(repo: UserSettingsRepository, user_id: str) -> None:
    settings = repo.get_or_create(user_id)
    if settings.get("kill_switch", False):
        raise APIError(
            "KILL_SWITCH_ON",
            "Kill switch is enabled",
            "Disable kill switch to run bot",
            status_code=403,
        )


@router.post("/bot/start", response_model=BotStateResponse)
async def start_bot(
    user_id: str | None = Query(default=None),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
):
    settings = get_settings()
    resolved_user_id = resolve_user_id(settings, x_user_id or user_id)
    repo = UserSettingsRepository(settings)
    repo.update(resolved_user_id, {"bot_state": "running"})
    return BotStateResponse(state="running")


@router.post("/bot/stop", response_model=BotStateResponse)
async def stop_bot(
    user_id: str | None = Query(default=None),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
):
    settings = get_settings()
    resolved_user_id = resolve_user_id(settings, x_user_id or user_id)
    repo = UserSettingsRepository(settings)
    repo.update(resolved_user_id, {"bot_state": "stopped"})
    return BotStateResponse(state="stopped")


@router.post("/bot/run-now", response_model=BotRunNowResponse)
async def run_bot_now(
    background_tasks: BackgroundTasks,
    user_id: str | None = Query(default=None),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
):
    settings = get_settings()
    resolved_user_id = resolve_user_id(settings, x_user_id or user_id)
    repo = UserSettingsRepository(settings)
    _ensure_not_killed(repo, resolved_user_id)
    runs_repo = BotRunsRepository(settings)
    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    repo.update(resolved_user_id, {"bot_state": "running", "next_run_at": plus_hours(1).isoformat()})
    runs_repo.create_run(resolved_user_id, run_id)
    background_tasks.add_task(_finalize_run, runs_repo, run_id)
    return BotRunNowResponse(run_id=run_id, state="queued")
