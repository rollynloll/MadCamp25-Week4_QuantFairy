from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List

import pandas as pd

from engine.data.protocol import DataProvider
from engine.errors import DataNotFoundError, DataSourceError, StrategyError
from engine.strategies.base import Strategy, StrategyContext, StrategySignal
from engine.strategies.sandbox import (
    PYTHON_ENTRYPOINT,
    StrategySandboxError,
    run_python_strategy_for_dates,
)
from engine.strategies.spec import PythonBody
from engine.strategies.validation import StrategyValidationError, validate_target_weights
from engine.backtest.metrics import compute_drawdown, compute_metrics, compute_returns


# 백테스트 실행 결과를 담는 데이터 클래스.
# runner.run()이 반환하는 유일한 출력 타입이다.
@dataclass
class BacktestResult:
    metrics: Dict[str, float]           # CAGR, Sharpe, MDD 등 성과 지표
    equity_curve: List[Dict[str, float]] # 날짜별 포트폴리오 가치 [{"date": "...", "equity": ...}]
    trade_stats: Dict[str, float]        # 거래 통계 (총 거래 횟수, 평균 보유 기간)
    benchmark: Dict | None               # 벤치마크 비교 데이터 (없으면 None)
    holdings_history: List[Dict]         # 월말 기준 보유 비중 스냅샷
    trade_log: List[Dict]                # 리밸런싱 날짜별 매매 기록 (날짜, 비중, equity, 턴오버)


# 진행 상황 콜백 타입.
# (stage: str, pct: float | None) 형식으로 호출된다.
# stage: "load_data" | "signals" | "simulate" | "metrics"
# pct: 0.0~1.0 진행률 (None이면 해당 단계의 시작만 알림)
ProgressCallback = Callable[[str, float | None], None]


def _rebalance_dates(dates: List[pd.Timestamp], freq: str) -> List[pd.Timestamp]:
    # 전체 거래일 목록에서 리밸런싱이 일어나야 할 날짜만 추출한다.
    # freq에 따라 다른 기준을 적용한다:
    #   "daily"  : 모든 날짜 (매일 리밸런싱)
    #   "weekly" : ISO 주 번호가 바뀌는 첫 날 (주간 첫 거래일)
    #   "monthly": (연도, 월) 조합이 바뀌는 첫 날 (월간 첫 거래일)
    # prev_marker를 이용해 기간 경계를 감지하고, 경계가 바뀔 때만 날짜를 선택한다.
    if not dates:
        return []
    if freq == "daily":
        return dates
    selected: List[pd.Timestamp] = []
    prev_marker = None
    for dt in dates:
        marker: object
        if freq == "weekly":
            marker = dt.isocalendar().week
        elif freq == "monthly":
            marker = (dt.year, dt.month)
        else:
            marker = dt   # 알 수 없는 freq는 매일로 처리
        if marker != prev_marker:
            selected.append(dt)
            prev_marker = marker
    return selected


def _benchmark_curve(
    prices_wide: pd.DataFrame,
    symbol: str,
    initial_cash: float,
    fee_bps: float,
    slippage_bps: float,
) -> List[Dict[str, float]]:
    # 벤치마크 심볼의 Buy-and-Hold 자산 곡선을 계산한다.
    # 첫 날 진입 시 (fee_bps + slippage_bps)만큼의 거래 비용이 차감된다.
    # 이후 매일 전일 대비 수익률을 누적하여 자산 가치를 추적한다.
    # 전략과 동일한 초기 자산과 거래 비용 가정을 적용하여 공정한 비교가 되도록 한다.
    if symbol not in prices_wide.columns:
        return []
    series = prices_wide[symbol].dropna()
    if series.empty:
        return []

    # 진입 시 거래 비용을 초기 자산에서 차감
    total_bps = (fee_bps + slippage_bps) / 10_000
    equity = initial_cash * (1 - total_bps)
    curve: List[Dict[str, float]] = []
    prev_price = None
    for dt, price in series.items():
        if prev_price is not None:
            equity *= price / prev_price   # 전일 대비 수익률 적용
        curve.append({"date": str(dt.date()), "equity": equity})
        prev_price = price
    return curve


def run(
    *,
    strategy: Strategy,
    data_provider: DataProvider,
    ctx: StrategyContext,
    universe: List[str],
    start_date: str,
    end_date: str,
    benchmark_symbol: str | None = None,
    initial_cash: float = 10_000.0,
    fee_bps: float = 0.0,
    slippage_bps: float = 0.0,
    rebalance_freq: str | None = None,
    long_only: bool = True,
    cash_buffer: float = 0.0,
    max_weight_per_asset: float = 1.0,
    python_body: PythonBody | None = None,
    progress_cb: ProgressCallback | None = None,
) -> BacktestResult:
    # 백테스트를 실행하고 BacktestResult를 반환한다.
    # 이 함수는 엔진의 핵심이며, 인프라(Supabase, FastAPI 등)에 전혀 의존하지 않는다.
    # 데이터는 data_provider를 통해 주입받고, 에러는 Python 표준 예외로만 발생시킨다.
    #
    # 실행 흐름:
    #   1. 파라미터 정규화 (리밸런싱 주기, 리스크 제약 결정)
    #   2. 데이터 로드 (data_provider.get_prices 호출)
    #   3. 데이터 형식 변환 (wide → MultiIndex, 전략에서 사용하는 형식)
    #   4. 신호 생성 (전략의 compute_target_weights 또는 generate_signals 호출)
    #   5. 포트폴리오 시뮬레이션 (날짜별 자산 가치 추적)
    #   6. 성과 지표 계산 및 반환
    #
    # python_body가 있으면 샌드박스에서 실행, 없으면 strategy 객체를 직접 호출한다.

    # --- 파라미터 정규화 ---

    # 리밸런싱 주기 결정 순서: 명시적 파라미터 > spec.rebalance.freq > ctx.params > 기본값
    freq = rebalance_freq
    if not freq and ctx.spec and ctx.spec.rebalance:
        freq = ctx.spec.rebalance.freq
    if not freq:
        freq = ctx.params.get("rebalance", "monthly")

    # 리스크 제약을 spec에서 가져온다 (spec이 있으면 spec 우선)
    if ctx.spec and ctx.spec.risk:
        risk = ctx.spec.risk
        long_only = risk.long_only
        cash_buffer = risk.cash_buffer
        max_weight_per_asset = risk.max_weight_per_asset

    # 벤치마크 심볼 정규화: 공백 제거, 대문자 변환, "CASH"는 None으로 처리
    benchmark_norm = benchmark_symbol.strip().upper() if benchmark_symbol else None
    if benchmark_norm == "CASH":
        benchmark_norm = None

    # 가격 데이터를 요청할 전체 심볼 목록 (universe + 벤치마크)
    symbols = list({*universe, *([benchmark_norm] if benchmark_norm else [])})

    # --- 데이터 로드 ---
    if progress_cb:
        progress_cb("load_data", None)
    try:
        # DataProvider 구현체(YFinance, DB 등)를 통해 가격 데이터를 가져온다
        prices_wide = data_provider.get_prices(symbols, start_date, end_date)
    except Exception as exc:
        # 네트워크 오류, DB 연결 실패 등 인프라 문제는 DataSourceError로 감싸서 전파
        raise DataSourceError(f"Failed to load prices: {exc}") from exc

    if prices_wide is None or prices_wide.empty:
        raise DataNotFoundError(f"No price data found for {symbols} ({start_date} to {end_date})")

    # universe 심볼 중 데이터가 없는 심볼은 조용히 제외하고 계속 진행한다.
    # 상장폐지·인수합병된 종목이 정적 유니버스에 섞여 있어도 백테스트가 죽지 않도록 한다.
    missing = [s for s in universe if s not in prices_wide.columns or prices_wide[s].isna().all()]
    if missing:
        universe = [s for s in universe if s not in missing]
        if not universe:
            raise DataNotFoundError(f"No price data found for any symbol in universe")

    # --- 데이터 형식 변환 ---
    # DataProvider는 wide 형식(컬럼=심볼)을 반환하지만,
    # 전략들은 MultiIndex(date, symbol) + adj_close 컬럼 형식을 기대한다.
    # stack()으로 열을 인덱스로 내려서 MultiIndex를 만든다.
    prices_df = (
        prices_wide.stack()
        .to_frame("adj_close")
        .rename_axis(["date", "symbol"])
    )

    # 시뮬레이션 루프에서는 wide 형식을 직접 사용한다 (인덱싱이 더 단순하다)
    price_matrix = prices_wide.sort_index()
    dates = list(price_matrix.index)

    # 비중 검증에 사용할 허용 심볼 집합: universe + params에 명시된 심볼들
    validation_universe = list({
        *universe,
        *([ctx.params.get("symbol", "").upper()] if ctx.params.get("symbol") else []),
        *([ctx.params.get("benchmark_symbol", "").upper()] if ctx.params.get("benchmark_symbol") else []),
        *([benchmark_norm] if benchmark_norm else []),
    })

    # --- 신호 생성 ---
    # 리밸런싱 날짜 목록을 계산하고, 각 날짜에 대해 전략 비중을 구한다.
    if progress_cb:
        progress_cb("signals", None)

    signals: List[StrategySignal] = []
    reb_dates = _rebalance_dates(dates, str(freq))

    try:
        if python_body is not None:
            # 사용자 제출 Python 전략: 샌드박스 프로세스에서 전체 리밸런싱 날짜를 한 번에 처리
            # timeout은 날짜 수에 비례하되 최소 12초, 최대 60초로 제한
            timeout_s = max(12.0, min(60.0, len(reb_dates) * 0.05))
            try:
                payloads = run_python_strategy_for_dates(
                    code=python_body.code,
                    entrypoint=python_body.entrypoint,
                    prices=prices_df,
                    ctx=ctx,
                    universe=universe,
                    rebalance_dates=reb_dates,
                    timeout_s=timeout_s,
                )
            except StrategySandboxError as exc:
                raise StrategyError(str(exc)) from exc

            for item in payloads:
                weights = item.get("target_weights") or {}
                if not weights:
                    continue
                try:
                    cleaned = validate_target_weights(
                        weights, validation_universe,
                        long_only=long_only,
                        cash_buffer=cash_buffer,
                        max_weight_per_asset=max_weight_per_asset,
                    )
                except StrategyValidationError as exc:
                    raise StrategyError(str(exc)) from exc
                signals.append(StrategySignal(date=str(item.get("date")), target_weights=cleaned))

        elif hasattr(strategy, "compute_target_weights"):
            # 날짜별 비중 계산 인터페이스 (LowVol, VolMomentum, RiskOnOff 등)
            # 각 리밸런싱 날짜마다 compute_target_weights를 호출한다.
            # NotImplementedError가 발생하면 generate_signals로 폴백한다.
            used = False
            try:
                for dt in reb_dates:
                    weights = strategy.compute_target_weights(prices_df, ctx, universe, dt)
                    if weights is None:
                        continue
                    try:
                        weights = validate_target_weights(
                            weights, validation_universe,
                            long_only=long_only,
                            cash_buffer=cash_buffer,
                            max_weight_per_asset=max_weight_per_asset,
                        )
                    except StrategyValidationError as exc:
                        raise StrategyError(str(exc)) from exc
                    signals.append(StrategySignal(date=str(dt.date()), target_weights=weights))
                used = True
            except NotImplementedError:
                used = False

            if not used:
                # compute_target_weights가 NotImplementedError를 발생시킨 경우
                # generate_signals로 폴백하여 전체 기간 신호를 한 번에 생성한다
                for signal in strategy.generate_signals(prices_df, ctx, universe):
                    try:
                        cleaned = validate_target_weights(
                            signal.target_weights, validation_universe,
                            long_only=long_only,
                            cash_buffer=cash_buffer,
                            max_weight_per_asset=max_weight_per_asset,
                        )
                    except StrategyValidationError as exc:
                        raise StrategyError(str(exc)) from exc
                    signals.append(StrategySignal(date=signal.date, target_weights=cleaned))
        else:
            # compute_target_weights 속성이 없는 전략 (generate_signals만 구현)
            for signal in strategy.generate_signals(prices_df, ctx, universe):
                try:
                    cleaned = validate_target_weights(
                        signal.target_weights, validation_universe,
                        long_only=long_only,
                        cash_buffer=cash_buffer,
                        max_weight_per_asset=max_weight_per_asset,
                    )
                except StrategyValidationError as exc:
                    raise StrategyError(str(exc)) from exc
                signals.append(StrategySignal(date=signal.date, target_weights=cleaned))

    except KeyError as exc:
        # 전략 내부에서 존재하지 않는 심볼에 접근할 때 발생
        missing_sym = str(exc.args[0]) if exc.args else "unknown"
        raise DataNotFoundError(f"Price data missing for symbol: {missing_sym}") from exc

    # --- 포트폴리오 시뮬레이션 ---
    # 신호를 날짜 → 비중 딕셔너리로 변환하여 O(1) 룩업을 가능하게 한다
    signal_map: Dict[pd.Timestamp, Dict[str, float]] = {
        pd.to_datetime(s.date): s.target_weights for s in signals
    }

    weights: Dict[str, float] = {}   # 현재 보유 비중 (비중 합 ≤ 1, 나머지는 현금)
    equity = initial_cash
    equity_curve: List[Dict[str, float]] = []
    turnover_days: List[str] = []    # 비중 변경이 일어난 날짜 목록 (거래 통계 계산용)
    holdings_history: List[Dict] = []
    trade_log: List[Dict] = []

    total = len(dates)
    stride = max(total // 50, 1)   # 진행률 콜백을 너무 자주 호출하지 않도록 보폭 설정
    if progress_cb and total:
        progress_cb("simulate", 0.0)

    prev_prices = None
    for idx, dt in enumerate(dates, start=1):
        # 오늘이 리밸런싱 날짜이면 비중을 업데이트하고 거래 비용을 차감한다
        if dt in signal_map:
            new_weights = signal_map[dt]

            # 턴오버 = 이전 비중과 새 비중의 절대 차이 합 (0~2 사이, 1이면 포트폴리오 전체 교체)
            turnover = sum(
                abs(new_weights.get(k, 0.0) - weights.get(k, 0.0))
                for k in set(new_weights) | set(weights)
            )

            # 거래 비용 = 턴오버 × (수수료 + 슬리피지) / 10,000 (bps → 소수)
            cost = turnover * (fee_bps + slippage_bps) / 10_000
            equity *= 1 - cost
            weights = new_weights
            if turnover > 0:
                turnover_days.append(str(dt.date()))

            # 리밸런싱 매매 기록: 날짜, 비중(비중 내림차순 정렬), equity, 턴오버
            sorted_weights = dict(
                sorted(((k, v) for k, v in weights.items() if v > 0), key=lambda x: -x[1])
            )
            trade_log.append({
                "date": str(dt.date()),
                "equity": round(equity, 2),
                "turnover_pct": round(turnover * 50, 1),  # 0~100% 단방향 기준
                "n_positions": len(sorted_weights),
                "weights": {k: round(v, 4) for k, v in sorted_weights.items()},
            })

        # 어제 대비 오늘의 자산 가치 변화를 계산한다
        if prev_prices is not None:
            daily_ret = 0.0
            for symbol, w in weights.items():
                if symbol not in price_matrix.columns:
                    continue
                prev_p = prev_prices.get(symbol)
                curr_p = price_matrix.loc[dt].get(symbol)
                # NaN이거나 데이터 없는 심볼은 수익률 0으로 처리 (포지션 동결)
                # bool(float('nan')) == True 이므로 반드시 pd.notna()로 명시 체크한다
                if prev_p and curr_p and pd.notna(prev_p) and pd.notna(curr_p):
                    daily_ret += w * (curr_p / prev_p - 1)
            equity *= 1 + daily_ret

        equity_curve.append({"date": str(dt.date()), "equity": equity})
        prev_prices = price_matrix.loc[dt].to_dict()

        # 월말에 현재 보유 비중을 스냅샷으로 기록한다 (UI의 월별 보유 현황 표시에 사용)
        if total:
            is_last = idx == total
            next_dt = dates[idx] if not is_last else None
            is_month_end = is_last or (
                next_dt is not None and next_dt.to_period("M") != dt.to_period("M")
            )
            if is_month_end:
                snapshot = {k: v for k, v in weights.items() if v != 0}
                holdings_history.append({"month": dt.strftime("%Y-%m"), "weights": snapshot})

        # 시뮬레이션 진행률 콜백 (약 50번 호출)
        if progress_cb and total and (idx % stride == 0 or idx == total):
            progress_cb("simulate", idx / total)

    # --- 성과 지표 계산 ---
    if progress_cb:
        progress_cb("metrics", None)

    bench_curve = None
    benchmark_payload = None
    if benchmark_norm:
        # 벤치마크 Buy-and-Hold 곡선을 계산하여 전략과 비교한다
        bench_curve = _benchmark_curve(
            price_matrix, benchmark_norm, initial_cash, fee_bps, slippage_bps
        )
        if bench_curve:
            benchmark_payload = {
                "symbol": benchmark_norm,
                "metrics": compute_metrics(bench_curve),
                "equity_curve": bench_curve,
                "returns": compute_returns(bench_curve),
                "drawdown": compute_drawdown(bench_curve),
            }

    # 평균 보유 기간: 연속된 리밸런싱 날짜 간격의 평균 (거래 빈도 파악에 사용)
    avg_hold_days = 0.0
    if len(turnover_days) > 1:
        spans = [
            (pd.to_datetime(turnover_days[i]) - pd.to_datetime(turnover_days[i - 1])).days
            for i in range(1, len(turnover_days))
        ]
        avg_hold_days = sum(spans) / len(spans)

    return BacktestResult(
        metrics=compute_metrics(equity_curve, benchmark_curve=bench_curve),
        equity_curve=equity_curve,
        trade_stats={
            "trades_count": len(turnover_days),    # 총 리밸런싱 횟수
            "avg_hold_days": avg_hold_days,        # 평균 보유 기간 (일)
        },
        benchmark=benchmark_payload,
        holdings_history=holdings_history,
        trade_log=trade_log,
    )
