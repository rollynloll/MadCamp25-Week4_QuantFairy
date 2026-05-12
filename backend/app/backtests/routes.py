from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Header, Query, status

from app.core.auth import resolve_my_user_id
from app.core.config import get_settings
from app.schemas.backtests import (
    BacktestCreateRequest,
    BacktestJob,
    BacktestListResponse,
    BacktestResultsResponse,
    BacktestValidateResponse,
)
from app.services.backtest_service import BacktestService

router = APIRouter()


def _svc(authorization: str | None) -> BacktestService:
    settings = get_settings()
    return BacktestService(settings, resolve_my_user_id(settings, authorization))


@router.post("/backtests/validate", response_model=BacktestValidateResponse)
async def validate_backtest(payload: BacktestCreateRequest, authorization: str | None = Header(default=None, alias="Authorization")):
    return _svc(authorization).validate(payload)


@router.post("/backtests", status_code=status.HTTP_201_CREATED, response_model=BacktestJob)
async def create_backtest(payload: BacktestCreateRequest, background_tasks: BackgroundTasks, authorization: str | None = Header(default=None, alias="Authorization")):
    return _svc(authorization).create(payload, background_tasks)


@router.get("/backtests", response_model=BacktestListResponse)
async def list_backtests(limit: int = Query(default=20, ge=1, le=100), cursor: str | None = Query(default=None), status_filter: str | None = Query(default=None, alias="status"), mode: str | None = Query(default=None), sort: str = Query(default="created_at"), order: str = Query(default="desc"), authorization: str | None = Header(default=None, alias="Authorization")):
    return _svc(authorization).list(limit, cursor, status_filter, mode, sort, order)


@router.get("/backtests/{backtest_id}", response_model=BacktestJob)
async def get_backtest(backtest_id: str, authorization: str | None = Header(default=None, alias="Authorization")):
    return _svc(authorization).get(backtest_id)


@router.get("/backtests/{backtest_id}/results", response_model=BacktestResultsResponse)
async def get_backtest_results(backtest_id: str, authorization: str | None = Header(default=None, alias="Authorization")):
    return _svc(authorization).get_results(backtest_id)


@router.post("/backtests/{backtest_id}/cancel", response_model=BacktestJob)
async def cancel_backtest(backtest_id: str, authorization: str | None = Header(default=None, alias="Authorization")):
    return _svc(authorization).cancel(backtest_id)


@router.delete("/backtests/{backtest_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backtest(backtest_id: str, authorization: str | None = Header(default=None, alias="Authorization")):
    _svc(authorization).delete(backtest_id)
