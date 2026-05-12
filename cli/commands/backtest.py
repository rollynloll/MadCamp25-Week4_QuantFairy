from __future__ import annotations

import json
from typing import List, Optional

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from cli.container import get_data_provider
from engine.backtest.runner import run
from engine.data.universe import list_sectors, resolve_universe, sector_display_name
from engine.strategies.base import StrategyContext
from engine.strategies.registry import get_strategy

app = typer.Typer(help="백테스트 실행")
console = Console()

_SECTOR_HELP = "섹터 필터 (" + ", ".join(list_sectors()) + ")"


@app.command("run")
def backtest_run(
    strategy: str = typer.Option(..., "--strategy", "-s", help="전략 entrypoint"),
    start: str = typer.Option(..., "--start", help="시작일 YYYY-MM-DD"),
    end: str = typer.Option(..., "--end", help="종료일 YYYY-MM-DD"),
    sector: Optional[str] = typer.Option(None, "--sector", help=_SECTOR_HELP),
    universe: Optional[str] = typer.Option(None, "--universe", help="티커 직접 지정 (쉼표 구분, --sector 무시)"),
    initial_cash: float = typer.Option(10_000.0, "--initial-cash", help="초기 자본금"),
    fee: float = typer.Option(0.0, "--fee", help="수수료 (bps)"),
    slippage: float = typer.Option(0.0, "--slippage", help="슬리피지 (bps)"),
    rebalance: Optional[str] = typer.Option(None, "--rebalance", help="리밸런싱 주기 (monthly/weekly/daily)"),
    param: Optional[List[str]] = typer.Option(None, "--param", help="전략 파라미터 key=value (여러 번 사용 가능)"),
    benchmark: Optional[str] = typer.Option(None, "--benchmark", help="벤치마크 티커 (예: SPY)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="결과 저장 경로 (.json)"),
    trades: bool = typer.Option(False, "--trades", help="리밸런싱 매매 기록 출력"),
    top_n: int = typer.Option(5, "--top-n", help="매매 기록에서 표시할 상위 종목 수"),
) -> None:
    """백테스트를 실행하고 성과 지표를 출력한다."""

    # --universe 파싱: 쉼표로 구분된 티커 문자열 → 리스트
    tickers = [t.strip() for t in universe.split(",")] if universe else None

    # 유니버스 결정 (직접 지정 > 섹터 > 전체 S&P 500)
    try:
        resolved = resolve_universe(universe=tickers, sector=sector)
    except ValueError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(1)

    # --param key=value 파싱
    extra_params: dict = {}
    for p in (param or []):
        if "=" not in p:
            console.print(f"[red]오류:[/red] --param 형식은 key=value 이어야 합니다: '{p}'")
            raise typer.Exit(1)
        k, v = p.split("=", 1)
        # 숫자면 숫자로 변환
        try:
            extra_params[k.strip()] = int(v)
        except ValueError:
            try:
                extra_params[k.strip()] = float(v)
            except ValueError:
                extra_params[k.strip()] = v.strip()

    # 전략 인스턴스 생성
    try:
        strategy_instance = get_strategy(strategy)
    except ValueError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(1)

    ctx = StrategyContext(params=extra_params)

    # 유니버스 출처 표시
    if tickers:
        universe_label = f"직접 지정 ({len(resolved)}개)"
    elif sector:
        universe_label = f"{sector_display_name(sector)} 섹터 ({len(resolved)}개)"
    else:
        universe_label = f"S&P 500 전체 ({len(resolved)}개)"

    console.print(f"\n[bold]백테스트 시작[/bold]")
    console.print(f"  전략    : {strategy}")
    console.print(f"  유니버스: {universe_label}")
    console.print(f"  기간    : {start} ~ {end}")
    if extra_params:
        console.print(f"  파라미터: {extra_params}")
    console.print()

    # 백테스트 실행
    _STAGE_LABEL = {
        "load_data": "데이터 로드 중...",
        "signals":   "신호 생성 중...",
        "simulate":  "시뮬레이션 중...",
        "metrics":   "지표 계산 중...",
    }
    # 각 단계 시작 시점의 기준 진행률 (simulate만 세부 진행률 있음)
    _STAGE_BASE = {"load_data": 0, "signals": 30, "simulate": 40, "metrics": 90}

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("준비 중...", total=100)

            def _on_progress(stage: str, pct: float | None) -> None:
                label = _STAGE_LABEL.get(stage, stage)
                base = _STAGE_BASE.get(stage, 0)
                if stage == "simulate" and pct is not None:
                    completed = base + int(pct * 50)  # 40 → 90
                else:
                    completed = base
                progress.update(task, description=label, completed=completed)

            result = run(
                strategy=strategy_instance,
                data_provider=get_data_provider(),
                ctx=ctx,
                universe=resolved,
                start_date=start,
                end_date=end,
                benchmark_symbol=benchmark,
                initial_cash=initial_cash,
                fee_bps=fee,
                slippage_bps=slippage,
                rebalance_freq=rebalance,
                progress_cb=_on_progress,
            )
            progress.update(task, description="완료", completed=100)
    except Exception as e:
        console.print(f"[red]백테스트 실패:[/red] {e}")
        raise typer.Exit(1)

    _print_metrics(result.metrics)

    if trades:
        _print_trade_log(result.trade_log, top_n=top_n)

    if output:
        _save_output(result, output)
        console.print(f"\n결과 저장됨: [cyan]{output}[/cyan]")


def _print_metrics(metrics: dict) -> None:
    table = Table(title="백테스트 결과", show_lines=True)
    table.add_column("지표", style="cyan", no_wrap=True)
    table.add_column("값", style="white", justify="right")

    labels = {
        "total_return_pct":    ("총 수익률",        "%"),
        "cagr_pct":            ("CAGR",             "%"),
        "volatility_pct":      ("연율화 변동성",     "%"),
        "sharpe":              ("샤프 비율",         ""),
        "max_drawdown_pct":    ("최대 낙폭 (MDD)",   "%"),
        "alpha_pct":           ("알파",              "%"),
        "beta":                ("베타",              ""),
        "tracking_error_pct":  ("트래킹 에러",       "%"),
        "information_ratio":   ("정보 비율",         ""),
        "turnover_pct":        ("평균 회전율",        "%"),
    }

    for key, (label, unit) in labels.items():
        val = metrics.get(key)
        if val is None:
            continue
        formatted = f"{val:+.2f}{unit}" if unit == "%" else f"{val:.4f}"
        table.add_row(label, formatted)

    console.print(table)


def _print_trade_log(trade_log: list, top_n: int = 5) -> None:
    if not trade_log:
        console.print("\n[yellow]매매 기록 없음[/yellow]")
        return

    table = Table(title=f"매매 기록 ({len(trade_log)}건)", show_lines=True)
    table.add_column("날짜",     style="cyan",  no_wrap=True)
    table.add_column("Equity",   style="white", justify="right")
    table.add_column("포지션 수", style="white", justify="right")
    table.add_column("턴오버",   style="yellow", justify="right")
    table.add_column(f"상위 {top_n}개 종목 (비중)", style="dim")

    for entry in trade_log:
        weights: dict = entry.get("weights", {})
        top_items = list(weights.items())[:top_n]
        holdings_str = "  ".join(f"{k}:{v*100:.1f}%" for k, v in top_items)
        if len(weights) > top_n:
            holdings_str += f"  [dim]+{len(weights) - top_n}개[/dim]"

        table.add_row(
            entry["date"],
            f"${entry['equity']:,.2f}",
            str(entry["n_positions"]),
            f"{entry['turnover_pct']:.1f}%",
            holdings_str,
        )

    console.print()
    console.print(table)


def _save_output(result, path: str) -> None:
    data = {
        "metrics": result.metrics,
        "equity_curve": result.equity_curve,
        "drawdown": result.drawdown,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
