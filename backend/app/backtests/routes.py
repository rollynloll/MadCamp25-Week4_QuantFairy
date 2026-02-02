from __future__ import annotations

import base64
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, Header, Query, status
from jsonschema import Draft7Validator

from app.benchmarks.data import BENCHMARKS
from app.core.auth import resolve_my_user_id
from app.core.config import get_settings
from app.core.errors import APIError
from app.core.time import now_kst
from app.schemas.backtests import (
    BacktestCreateRequest,
    BacktestJob,
    BacktestListResponse,
    BacktestResultsResponse,
    BacktestValidateResponse,
)
from app.services.backtest_engine import StrategyContext, run_ensemble_backtest, run_single_backtest
from app.services.backtest_runner import run_backtest
from app.services.data_provider import load_price_series, parse_date, trading_days
from app.services.metrics import compute_drawdown, compute_metrics, compute_returns
from app.storage.backtests_store import STORE
from app.storage.backtest_runs_repo import BacktestRunsRepository
from app.storage.my_strategies_repo import MyStrategiesRepository
from app.storage.public_strategies_repo import PublicStrategiesRepository
from app.universes.presets import UNIVERSE_PRESETS


router = APIRouter()


def _update_job_state(
    backtest_id: str,
    *,
    status_value: str | None = None,
    progress: int | None = None,
    error: Dict[str, Any] | None = None,
) -> None:
    updates: Dict[str, Any] = {"updated_at": now_kst().isoformat()}
    if status_value is not None:
        updates["status"] = status_value
    if progress is not None:
        updates["progress"] = progress
    if error is not None:
        updates["error"] = error
    STORE.update_job(backtest_id, updates)


def _job_is_canceled(backtest_id: str) -> bool:
    job = STORE.get_job(backtest_id)
    return not job or job.get("status") == "canceled"


def _run_backtest_job(
    *,
    backtest_id: str,
    payload: BacktestCreateRequest,
    user_id: str,
    universe_tickers: List[str],
    strategy_contexts: List[StrategyContext],
    spec_dict: Dict[str, Any],
    benchmark_refs: List[Dict[str, Any]],
    baseline_benchmark_curve: List[Dict[str, float]] | None,
) -> None:
    _update_job_state(backtest_id, status_value="running", progress=5)

    try:
        results_payload: Dict[str, Any] = {}
        result_items: List[tuple[StrategyRef, StrategyContext, Dict[str, Any]]] = []
        benchmark_symbol = benchmark_refs[0]["symbol"] if benchmark_refs else None

        settings = get_settings()
        public_repo = PublicStrategiesRepository(settings)
        my_repo = MyStrategiesRepository(settings)
        public_repo.ensure_seed()

        def resolve_runtime(ref: StrategyRef) -> Dict[str, Any]:
            if ref.type == "public":
                public_row = public_repo.get(ref.id)
                if not public_row:
                    raise APIError("NOT_FOUND", "Public strategy not found", status_code=404)
                entrypoint = public_row.get("entrypoint")
                if not entrypoint:
                    raise APIError("VALIDATION_ERROR", "Missing entrypoint", status_code=422)
                return {
                    "entrypoint": entrypoint,
                    "code_version": public_row.get("code_version") or "unknown",
                    "public_strategy_id": public_row.get("public_strategy_id", ref.id),
                    "public_version_snapshot": public_row.get("version"),
                }

            my_row = my_repo.get(user_id, ref.id)
            if not my_row:
                raise APIError("NOT_FOUND", "My strategy not found", status_code=404)
            public_id = my_row.get("source_public_strategy_id")
            public_row = public_repo.get(public_id) if public_id else None
            entrypoint = my_row.get("entrypoint_snapshot") or (public_row.get("entrypoint") if public_row else None)
            if not entrypoint:
                raise APIError("VALIDATION_ERROR", "Missing entrypoint", status_code=422)
            code_version = my_row.get("code_version_snapshot") or (public_row.get("code_version") if public_row else None) or "unknown"
            public_version_snapshot = my_row.get("public_version_snapshot") or (public_row.get("version") if public_row else None)
            return {
                "entrypoint": entrypoint,
                "code_version": code_version,
                "public_strategy_id": public_id,
                "public_version_snapshot": public_version_snapshot,
                "my_row": my_row,
            }

        def build_item_from_run(ref: StrategyRef, ctx: StrategyContext) -> Dict[str, Any]:
            runtime = resolve_runtime(ref)
            run_params = dict(ctx.params)
            if (
                "universe" not in run_params
                and "universe_preset" not in run_params
                and "symbol" not in run_params
            ):
                if spec_dict.get("universe", {}).get("type") == "CUSTOM":
                    run_params["universe"] = spec_dict.get("universe", {}).get("tickers") or []
                else:
                    run_params["universe_preset"] = spec_dict.get("universe", {}).get("preset_id")
            run_result = run_backtest(
                my_strategy_id=ref.id,
                user_id=user_id,
                params=run_params,
                entrypoint=runtime["entrypoint"],
                code_version=runtime["code_version"],
                start_date=spec_dict["period_start"],
                end_date=spec_dict["period_end"],
                benchmark_symbol=benchmark_symbol,
                initial_cash=spec_dict["initial_cash"],
                fee_bps=spec_dict["fee_bps"],
                slippage_bps=spec_dict["slippage_bps"],
            )
            equity_curve = run_result.equity_curve
            trade_count = run_result.trade_stats.get("trades_count", 0) if run_result.trade_stats else 0
            return {
                "label": ctx.label,
                "strategy_ref": ref.model_dump(),
                "metrics": run_result.metrics,
                "equity_curve": equity_curve,
                "returns": compute_returns(equity_curve),
                "drawdown": compute_drawdown(equity_curve),
                "positions_summary": {
                    "avg_positions": 1 if trade_count else 0,
                    "max_positions": 1 if trade_count else 0,
                },
            }

        if payload.mode == "single":
            _update_job_state(backtest_id, progress=15)
            ctx = strategy_contexts[0]
            item = build_item_from_run(payload.strategies[0], ctx)
            results_payload["results"] = [item]
            result_items.append((payload.strategies[0], ctx, results_payload["results"][0]))
            _update_job_state(backtest_id, progress=85)
        elif payload.mode == "batch":
            results = []
            total = max(len(strategy_contexts), 1)
            for idx, (ref, ctx) in enumerate(zip(payload.strategies, strategy_contexts), start=1):
                if _job_is_canceled(backtest_id):
                    return
                progress = 10 + int((idx - 1) / total * 60)
                _update_job_state(backtest_id, progress=progress)
                results.append(build_item_from_run(ref, ctx))
                result_items.append((ref, ctx, results[-1]))
            results_payload["results"] = results
            comparison_table = []
            for item in results:
                metrics = item["metrics"]
                comparison_table.append(
                    {
                        "label": item["label"],
                        "total_return_pct": metrics.get("total_return_pct", 0.0),
                        "cagr_pct": metrics.get("cagr_pct", 0.0),
                        "sharpe": metrics.get("sharpe", 0.0),
                        "max_drawdown_pct": metrics.get("max_drawdown_pct", 0.0),
                    }
                )
            results_payload["comparison_table"] = comparison_table
            _update_job_state(backtest_id, progress=85)
        else:
            if _job_is_canceled(backtest_id):
                return
            _update_job_state(backtest_id, progress=20)
            ensemble_spec = payload.ensemble.model_dump() if payload.ensemble else {}
            ensemble_result = run_ensemble_backtest(
                spec_dict,
                strategy_contexts,
                universe_tickers,
                ensemble_spec,
                benchmark_curve=baseline_benchmark_curve,
            )
            results_payload["ensemble_result"] = {
                "label": "ensemble",
                "strategy_ref": payload.strategies[0].model_dump(),
                **ensemble_result,
            }
            component_results = []
            total = max(len(strategy_contexts), 1)
            for idx, (ref, ctx) in enumerate(zip(payload.strategies, strategy_contexts), start=1):
                if _job_is_canceled(backtest_id):
                    return
                progress = 40 + int((idx - 1) / total * 40)
                _update_job_state(backtest_id, progress=progress)
                item = run_single_backtest(
                    spec_dict, ctx, universe_tickers, benchmark_curve=baseline_benchmark_curve
                )
                component_results.append(
                    {
                        "label": ctx.label,
                        "strategy_ref": ref.model_dump(),
                        **item,
                    }
                )
                result_items.append((ref, ctx, component_results[-1]))
            results_payload["components"] = component_results
            _update_job_state(backtest_id, progress=85)

        if _job_is_canceled(backtest_id):
            return

        if benchmark_refs:
            _update_job_state(backtest_id, progress=90)
            results_payload["benchmarks"] = _build_benchmarks_payload(benchmark_refs, spec_dict)
            _update_job_state(backtest_id, progress=95)

        if result_items:
            if _job_is_canceled(backtest_id):
                return
            runs_repo = BacktestRunsRepository(settings)
            benchmark_item = None
            if isinstance(results_payload.get("benchmarks"), dict):
                benchmark_items = results_payload["benchmarks"].get("items") or []
                if benchmark_items:
                    benchmark_item = benchmark_items[0]
            for ref, ctx, result in result_items:
                if ref.type != "my":
                    continue
                runtime = resolve_runtime(ref)
                my_row = runtime.get("my_row")
                public_id = runtime.get("public_strategy_id")
                entrypoint = runtime.get("entrypoint")
                code_version = runtime.get("code_version")
                public_version_snapshot = runtime.get("public_version_snapshot")
                runs_repo.create(
                    {
                        "run_id": f"run_{uuid.uuid4().hex}",
                        "user_id": user_id,
                        "my_strategy_id": ref.id,
                        "public_strategy_id": public_id,
                        "entrypoint": entrypoint,
                        "code_version": code_version or "unknown",
                        "public_version_snapshot": public_version_snapshot,
                        "params": ctx.params,
                        "start_date": spec_dict["period_start"],
                        "end_date": spec_dict["period_end"],
                        "benchmark_symbol": benchmark_item.get("symbol") if benchmark_item else None,
                        "initial_cash": spec_dict["initial_cash"],
                        "fee_bps": spec_dict["fee_bps"],
                        "slippage_bps": spec_dict["slippage_bps"],
                        "status": "done",
                        "metrics": result.get("metrics") or {},
                        "equity_curve": result.get("equity_curve") or [],
                        "trade_stats": result.get("trade_stats") or {},
                        "benchmark": benchmark_item,
                    }
                )

        STORE.set_results(backtest_id, results_payload)
        _update_job_state(backtest_id, status_value="done", progress=100)
    except APIError as exc:
        _update_job_state(
            backtest_id,
            status_value="failed",
            progress=100,
            error={
                "code": exc.code,
                "message": exc.message,
                "detail": exc.detail,
                "details": exc.details,
            },
        )
    except Exception as exc:
        _update_job_state(
            backtest_id,
            status_value="failed",
            progress=100,
            error={
                "code": "INTERNAL_ERROR",
                "message": "Unexpected error",
                "detail": str(exc),
            },
        )


def _encode_cursor(value: str) -> str:
    raw = value.encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def _decode_cursor(cursor: str | None) -> str | None:
    if not cursor:
        return None
    try:
        return base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
    except Exception:
        return None


def _validate_json_schema(schema: dict, params: dict, field_prefix: str) -> List[Dict[str, str]]:
    validator = Draft7Validator(schema)
    errors: List[Dict[str, str]] = []
    for error in validator.iter_errors(params):
        path = ".".join([str(p) for p in error.path])
        field = field_prefix if not path else f"{field_prefix}.{path}"
        errors.append({"field": field, "reason": error.message})
    return errors


def _resolve_universe_tickers(spec) -> List[str]:
    if spec.universe.type == "PRESET":
        preset = UNIVERSE_PRESETS.get(spec.universe.preset_id or "")
        if not preset:
            raise APIError(
                "VALIDATION_ERROR",
                "Invalid preset_id",
                details=[{"field": "spec.universe.preset_id", "reason": "unknown preset"}],
                status_code=422,
            )
        return preset["tickers"]
    tickers = spec.universe.tickers or []
    return [t.strip().upper() for t in tickers if t and t.strip()]


def _validate_spec(payload: BacktestCreateRequest) -> List[Dict[str, str]]:
    errors: List[Dict[str, str]] = []
    try:
        start = parse_date(payload.spec.period_start)
    except Exception:
        errors.append({"field": "spec.period_start", "reason": "invalid date"})
        start = None
    try:
        end = parse_date(payload.spec.period_end)
    except Exception:
        errors.append({"field": "spec.period_end", "reason": "invalid date"})
        end = None

    if start and end and start > end:
        errors.append({"field": "spec.period_start", "reason": "must be <= period_end"})

    if payload.spec.initial_cash <= 0:
        errors.append({"field": "spec.initial_cash", "reason": "must be > 0"})
    if payload.spec.fee_bps < 0:
        errors.append({"field": "spec.fee_bps", "reason": "must be >= 0"})
    if payload.spec.slippage_bps < 0:
        errors.append({"field": "spec.slippage_bps", "reason": "must be >= 0"})

    if payload.spec.universe.type == "PRESET":
        if not payload.spec.universe.preset_id:
            errors.append({"field": "spec.universe.preset_id", "reason": "required"})
        elif payload.spec.universe.preset_id not in UNIVERSE_PRESETS:
            errors.append({"field": "spec.universe.preset_id", "reason": "unknown preset"})
    else:
        tickers = payload.spec.universe.tickers or []
        if not tickers:
            errors.append({"field": "spec.universe.tickers", "reason": "required"})
        elif len(tickers) < 1 or len(tickers) > 500:
            errors.append({"field": "spec.universe.tickers", "reason": "size must be 1..500"})

    mode = payload.mode
    if mode == "single" and len(payload.strategies) != 1:
        errors.append({"field": "strategies", "reason": "must contain exactly 1 strategy"})
    if mode == "batch" and len(payload.strategies) < 2:
        errors.append({"field": "strategies", "reason": "must contain at least 2 strategies"})
    if mode == "ensemble" and len(payload.strategies) < 2:
        errors.append({"field": "strategies", "reason": "must contain at least 2 strategies"})
    if mode == "ensemble":
        if not payload.ensemble or not payload.ensemble.weights:
            errors.append({"field": "ensemble.weights", "reason": "required"})
    if payload.benchmarks:
        supported = {item["symbol"] for item in BENCHMARKS}
        for idx, bench in enumerate(payload.benchmarks):
            if bench.symbol not in supported:
                errors.append(
                    {
                        "field": f"benchmarks[{idx}].symbol",
                        "reason": "unsupported benchmark",
                    }
                )

    return errors


def _resolve_strategy_contexts(
    payload: BacktestCreateRequest,
    user_id: str,
) -> List[StrategyContext]:
    settings = get_settings()
    public_repo = PublicStrategiesRepository(settings)
    my_repo = MyStrategiesRepository(settings)
    public_repo.ensure_seed()

    contexts: List[StrategyContext] = []
    errors: List[Dict[str, str]] = []

    for idx, ref in enumerate(payload.strategies):
        if ref.type == "public":
            public_row = public_repo.get(ref.id)
            if not public_row:
                raise APIError("NOT_FOUND", "Public strategy not found", status_code=404)
            schema = public_row.get("param_schema", {}) or {}
            base_params = public_row.get("default_params", {}) or {}
            label = ref.label or public_row.get("name", ref.id)
        else:
            my_row = my_repo.get(user_id, ref.id)
            if not my_row:
                raise APIError("NOT_FOUND", "My strategy not found", status_code=404)
            public_row = public_repo.get(my_row.get("source_public_strategy_id", ""))
            if not public_row:
                raise APIError("NOT_FOUND", "Public strategy not found", status_code=404)
            schema = public_row.get("param_schema", {}) or {}
            base_params = my_row.get("params", {}) or {}
            label = ref.label or my_row.get("name", ref.id)

        params = {**base_params, **(ref.params_override or {})}
        if schema:
            errors.extend(
                _validate_json_schema(
                    schema,
                    params,
                    field_prefix=f"strategies[{idx}].params",
                )
            )
        contexts.append(StrategyContext(strategy_id=ref.id, params=params, label=label))

    if errors:
        raise APIError(
            "VALIDATION_ERROR",
            "Invalid params",
            details=errors,
            status_code=422,
        )

    if payload.mode == "ensemble" and payload.ensemble and payload.ensemble.weights:
        weight_keys = set(payload.ensemble.weights.keys())
        for ref in payload.strategies:
            if ref.id not in weight_keys:
                errors.append(
                    {
                        "field": f"ensemble.weights.{ref.id}",
                        "reason": "missing weight for strategy",
                    }
                )
        if errors:
            raise APIError(
                "VALIDATION_ERROR",
                "Invalid params",
                details=errors,
                status_code=422,
            )

    return contexts


def _build_benchmark_curve(symbol: str, spec: dict) -> List[Dict[str, float]]:
    if symbol.upper() == "CASH":
        curve = []
        for d in trading_days(parse_date(spec["period_start"]), parse_date(spec["period_end"])):
            curve.append({"date": d.isoformat(), "equity": spec["initial_cash"]})
        return curve

    prices = load_price_series([symbol], spec["period_start"], spec["period_end"], spec.get("price_field", "adj_close"))
    series = prices.get(symbol, {})
    if not series:
        return []
    dates = list(series.keys())
    equity = spec["initial_cash"]
    curve = []
    prev_price = None
    for date in dates:
        price = series.get(date)
        if prev_price is not None and price:
            equity *= price / prev_price
        curve.append({"date": date, "equity": equity})
        prev_price = price
    return curve


def _build_benchmarks_payload(benchmarks: List[Dict[str, Any]], spec: dict) -> Dict[str, Any]:
    items = []
    for ref in benchmarks:
        symbol = ref["symbol"]
        curve = _build_benchmark_curve(symbol, spec)
        metrics = compute_metrics(curve)
        item = {
            "symbol": symbol,
            "label": ref.get("label") or symbol,
            "metrics": metrics,
            "equity_curve": curve,
            "returns": compute_returns(curve),
            "drawdown": compute_drawdown(curve),
        }
        items.append(item)
    return {"items": items}


def _get_baseline_benchmark_curve(benchmarks: List[Dict[str, Any]] | None, spec: dict) -> List[Dict[str, float]] | None:
    if not benchmarks:
        return None
    return _build_benchmark_curve(benchmarks[0]["symbol"], spec)


def _validate_and_prepare(payload: BacktestCreateRequest, user_id: str):
    errors = _validate_spec(payload)
    if errors:
        raise APIError(
            "VALIDATION_ERROR",
            "Invalid params",
            details=errors,
            status_code=422,
        )
    universe_tickers = _resolve_universe_tickers(payload.spec)
    if not universe_tickers:
        raise APIError(
            "VALIDATION_ERROR",
            "Invalid universe",
            details=[{"field": "spec.universe", "reason": "no tickers resolved"}],
            status_code=422,
        )
    strategy_contexts = _resolve_strategy_contexts(payload, user_id)
    return universe_tickers, strategy_contexts


@router.post("/backtests/validate", response_model=BacktestValidateResponse)
async def validate_backtest(
    payload: BacktestCreateRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    settings = get_settings()
    user_id = resolve_my_user_id(settings, authorization)
    _validate_and_prepare(payload, user_id)
    return BacktestValidateResponse(valid=True, errors=[])


@router.post("/backtests", status_code=status.HTTP_201_CREATED, response_model=BacktestJob)
async def create_backtest(
    payload: BacktestCreateRequest,
    background_tasks: BackgroundTasks,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    settings = get_settings()
    user_id = resolve_my_user_id(settings, authorization)
    universe_tickers, strategy_contexts = _validate_and_prepare(payload, user_id)

    spec_dict = payload.spec.model_dump()
    benchmark_refs = [b.model_dump() for b in payload.benchmarks] if payload.benchmarks else []
    baseline_benchmark_curve = _get_baseline_benchmark_curve(benchmark_refs, spec_dict)

    now = now_kst().isoformat()
    job = {
        "backtest_id": f"bt_{uuid.uuid4().hex}",
        "user_id": user_id,
        "mode": payload.mode,
        "status": "queued",
        "progress": 0,
        "spec": spec_dict,
        "strategies": [s.model_dump() for s in payload.strategies],
        "benchmarks": benchmark_refs or None,
        "created_at": now,
        "updated_at": now,
    }
    STORE.create_job(job)

    background_tasks.add_task(
        _run_backtest_job,
        backtest_id=job["backtest_id"],
        payload=payload,
        user_id=user_id,
        universe_tickers=universe_tickers,
        strategy_contexts=strategy_contexts,
        spec_dict=spec_dict,
        benchmark_refs=benchmark_refs,
        baseline_benchmark_curve=baseline_benchmark_curve,
    )

    return {k: v for k, v in job.items() if k != "user_id"}


@router.get("/backtests", response_model=BacktestListResponse)
async def list_backtests(
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    mode: str | None = Query(default=None),
    sort: str = Query(default="created_at"),
    order: str = Query(default="desc"),
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    settings = get_settings()
    user_id = resolve_my_user_id(settings, authorization)
    if sort not in {"created_at", "updated_at"}:
        raise APIError("VALIDATION_ERROR", "Invalid sort", status_code=400)
    if order not in {"asc", "desc"}:
        raise APIError("VALIDATION_ERROR", "Invalid order", status_code=400)

    items = STORE.list_jobs(
        user_id,
        {"status": status_filter, "mode": mode},
        sort,
        order,
    )
    cursor_value = _decode_cursor(cursor)
    if cursor_value:
        if order == "desc":
            items = [item for item in items if str(item.get(sort, "")) < cursor_value]
        else:
            items = [item for item in items if str(item.get(sort, "")) > cursor_value]

    next_cursor = None
    sliced = items[: limit + 1]
    if len(sliced) > limit:
        last = sliced[limit - 1]
        next_cursor = _encode_cursor(str(last.get(sort, "")))
        sliced = sliced[:limit]

    response_items = [{k: v for k, v in item.items() if k != "user_id"} for item in sliced]
    return {"items": response_items, "next_cursor": next_cursor}


@router.get("/backtests/{backtest_id}", response_model=BacktestJob)
async def get_backtest(
    backtest_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    settings = get_settings()
    user_id = resolve_my_user_id(settings, authorization)
    job = STORE.get_job(backtest_id)
    if not job or job.get("user_id") != user_id:
        raise APIError("NOT_FOUND", "Backtest not found", status_code=404)
    return {k: v for k, v in job.items() if k != "user_id"}


@router.get("/backtests/{backtest_id}/results", response_model=BacktestResultsResponse)
async def get_backtest_results(
    backtest_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    settings = get_settings()
    user_id = resolve_my_user_id(settings, authorization)
    job = STORE.get_job(backtest_id)
    if not job or job.get("user_id") != user_id:
        raise APIError("NOT_FOUND", "Backtest not found", status_code=404)
    if job.get("status") != "done":
        raise APIError("CONFLICT", "Backtest not completed", status_code=409)
    results = STORE.get_results(backtest_id)
    if not results:
        raise APIError("NOT_FOUND", "Backtest results not found", status_code=404)
    return {
        "backtest_id": backtest_id,
        "status": job.get("status"),
        **results,
    }


@router.post("/backtests/{backtest_id}/cancel", response_model=BacktestJob)
async def cancel_backtest(
    backtest_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    settings = get_settings()
    user_id = resolve_my_user_id(settings, authorization)
    job = STORE.get_job(backtest_id)
    if not job or job.get("user_id") != user_id:
        raise APIError("NOT_FOUND", "Backtest not found", status_code=404)
    if job.get("status") not in {"queued", "running"}:
        raise APIError("CONFLICT", "Backtest cannot be canceled", status_code=409)
    updated = STORE.update_job(
        backtest_id,
        {"status": "canceled", "updated_at": now_kst().isoformat()},
    )
    return {k: v for k, v in (updated or job).items() if k != "user_id"}


@router.delete("/backtests/{backtest_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backtest(
    backtest_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    settings = get_settings()
    user_id = resolve_my_user_id(settings, authorization)
    job = STORE.get_job(backtest_id)
    if not job or job.get("user_id") != user_id:
        raise APIError("NOT_FOUND", "Backtest not found", status_code=404)
    if job.get("status") in {"queued", "running"}:
        raise APIError("CONFLICT", "Backtest cannot be deleted", status_code=409)
    STORE.delete(backtest_id)
    return None
