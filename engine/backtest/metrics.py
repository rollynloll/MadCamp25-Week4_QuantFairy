from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple


def compute_returns(equity_curve: List[Dict[str, float]]) -> List[Dict[str, float]]:
    # 자산 곡선(equity_curve)에서 일간 수익률 시계열을 계산한다.
    # equity_curve는 [{"date": "2020-01-02", "equity": 10050.0}, ...] 형식이다.
    # 첫 번째 포인트는 기준값이므로 수익률 계산에서 제외된다 (N개 포인트 → N-1개 수익률).
    # 반환값: [{"date": "2020-01-03", "ret": 0.005}, ...] (ret = 일간 수익률, 소수)
    returns: List[Dict[str, float]] = []
    prev = None
    for point in equity_curve:
        equity = point["equity"]
        if prev is None:
            prev = equity
            continue
        ret = (equity / prev - 1.0) if prev else 0.0
        returns.append({"date": point["date"], "ret": ret})
        prev = equity
    return returns


def compute_drawdown(equity_curve: List[Dict[str, float]]) -> List[Dict[str, float]]:
    # 각 날짜의 고점 대비 낙폭(Drawdown)을 퍼센트로 계산한다.
    # 고점은 그 시점까지의 최고 자산 가치를 추적하여 갱신한다.
    # 반환값: [{"date": "...", "dd_pct": -5.2}, ...] (dd_pct = 음수, 고점 대비 하락률 %)
    # MDD(Maximum Drawdown)는 반환 리스트에서 dd_pct의 최솟값이다.
    drawdown: List[Dict[str, float]] = []
    peak = None
    for point in equity_curve:
        equity = point["equity"]
        if peak is None or equity > peak:
            peak = equity   # 새로운 고점 갱신
        dd = (equity - peak) / peak * 100 if peak else 0.0
        drawdown.append({"date": point["date"], "dd_pct": dd})
    return drawdown


def _stats(returns: List[float]) -> Tuple[float, float]:
    # 수익률 리스트의 평균(mean)과 표준편차(std)를 반환한다.
    # 표준편차는 모집단 표준편차(N으로 나눔)를 사용한다.
    # 빈 리스트이면 (0.0, 0.0)을 반환한다.
    if not returns:
        return 0.0, 0.0
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / len(returns)
    return mean, math.sqrt(var)


def compute_metrics(
    equity_curve: List[Dict[str, float]],
    benchmark_curve: Optional[List[Dict[str, float]]] = None,
    turnover_pct: float = 0.0,
) -> Dict[str, float]:
    # 자산 곡선에서 주요 성과 지표를 계산하여 딕셔너리로 반환한다.
    # benchmark_curve가 주어지면 알파, 베타, 정보 비율 등 벤치마크 대비 지표도 계산한다.
    #
    # 계산되는 지표:
    #   total_return_pct   : 전체 기간 총 수익률 (%)
    #   cagr_pct           : 연평균 복합 성장률 (%, 252 거래일 기준)
    #   volatility_pct     : 연율화 변동성 (%, 일간 표준편차 × √252)
    #   sharpe             : 샤프 비율 (무위험 수익률 0 가정, 연율화)
    #   max_drawdown_pct   : 최대 낙폭 (%, 음수)
    #   alpha_pct          : 벤치마크 대비 초과 수익률 연율화 (%)
    #   beta               : 벤치마크에 대한 민감도 (공분산 / 벤치마크 분산)
    #   tracking_error_pct : 벤치마크 대비 초과 수익률의 표준편차 연율화 (%)
    #   information_ratio  : 초과 수익률 / tracking_error (위험 대비 초과 성과)
    #   turnover_pct       : 평균 일간 회전율 (호출자가 외부에서 전달)

    if not equity_curve:
        return {
            "total_return_pct": 0.0,
            "cagr_pct": 0.0,
            "volatility_pct": 0.0,
            "sharpe": 0.0,
            "max_drawdown_pct": 0.0,
            "alpha_pct": 0.0,
            "beta": 0.0,
            "tracking_error_pct": 0.0,
            "information_ratio": 0.0,
            "turnover_pct": turnover_pct,
        }

    # 시작 대비 최종 자산 가치로 총 수익률 계산
    total_return_pct = (equity_curve[-1]["equity"] / equity_curve[0]["equity"] - 1) * 100

    returns = [item["ret"] for item in compute_returns(equity_curve)]
    mean, std = _stats(returns)

    # 일간 표준편차에 √252를 곱해 연율화 변동성으로 변환
    volatility_pct = std * math.sqrt(252) * 100 if std else 0.0

    # 샤프 비율: 연율화 수익률 / 연율화 변동성 (무위험 수익률 = 0 가정)
    sharpe = (mean / std * math.sqrt(252)) if std else 0.0

    # CAGR: (최종자산/초기자산)^(252/기간일수) - 1
    # 252 거래일 = 1년으로 가정하여 연율화
    periods = max(len(returns), 1)
    cagr_pct = ((equity_curve[-1]["equity"] / equity_curve[0]["equity"]) ** (252 / periods) - 1) * 100

    drawdown = compute_drawdown(equity_curve)
    max_drawdown_pct = min((d["dd_pct"] for d in drawdown), default=0.0)

    # 벤치마크 대비 지표 (benchmark_curve가 있을 때만 계산)
    alpha_pct = 0.0
    beta = 0.0
    tracking_error_pct = 0.0
    information_ratio = 0.0

    if benchmark_curve:
        bench_returns = [item["ret"] for item in compute_returns(benchmark_curve)]
        if bench_returns:
            mean_b, std_b = _stats(bench_returns)

            # 베타 = Cov(전략 수익률, 벤치마크 수익률) / Var(벤치마크 수익률)
            cov = sum(
                (r - mean) * (b - mean_b)
                for r, b in zip(returns, bench_returns)
            ) / len(bench_returns)
            beta = cov / (std_b ** 2) if std_b else 0.0

            # 알파 = 전략 수익률 - β × 벤치마크 수익률 (연율화)
            alpha_pct = ((mean - beta * mean_b) * 252) * 100

            # 초과 수익률(active return) 시계열의 표준편차로 tracking error 계산
            diff = [r - b for r, b in zip(returns, bench_returns)]
            mean_diff, std_diff = _stats(diff)
            tracking_error_pct = std_diff * math.sqrt(252) * 100 if std_diff else 0.0

            # 정보 비율 = 연율화 초과 수익률 / tracking error
            information_ratio = (
                mean_diff / std_diff * math.sqrt(252) if std_diff else 0.0
            )

    return {
        "total_return_pct": total_return_pct,
        "cagr_pct": cagr_pct,
        "volatility_pct": volatility_pct,
        "sharpe": sharpe,
        "max_drawdown_pct": max_drawdown_pct,
        "alpha_pct": alpha_pct,
        "beta": beta,
        "tracking_error_pct": tracking_error_pct,
        "information_ratio": information_ratio,
        "turnover_pct": turnover_pct,
    }
