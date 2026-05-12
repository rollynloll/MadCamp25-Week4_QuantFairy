from __future__ import annotations

from datetime import date
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

from cli.container import get_broker, get_data_provider
from cli.state import get_last_rebalance, make_state_key, set_last_rebalance
from engine.data.universe import list_sectors, resolve_universe, sector_display_name
from engine.strategies.base import StrategyContext
from engine.strategies.registry import get_strategy
from engine.trading.scheduler import run_live

app = typer.Typer(help="자동매매 실행")
console = Console()

_SECTOR_HELP = "섹터 필터 (" + ", ".join(list_sectors()) + ")"

# 리밸런싱 주기별 NYSE 기준 실행 시각 (APScheduler cron 인수)
# 장 개시(9:30 ET) 후 35분 뒤에 실행해 오프닝 변동성을 피한다.
_CRON_ARGS = {
    "monthly": dict(day=1,             day_of_week="mon-fri", hour=9, minute=35),
    "weekly":  dict(day_of_week="mon",                        hour=9, minute=35),
    "daily":   dict(day_of_week="mon-fri",                    hour=9, minute=35),
}


# ──────────────────────────────────────────────
# 공유 로직
# ──────────────────────────────────────────────

def _parse_params(param: List[str] | None) -> dict:
    extra: dict = {}
    for p in (param or []):
        if "=" not in p:
            raise ValueError(f"--param 형식은 key=value 이어야 합니다: '{p}'")
        k, v = p.split("=", 1)
        try:
            extra[k.strip()] = int(v)
        except ValueError:
            try:
                extra[k.strip()] = float(v)
            except ValueError:
                extra[k.strip()] = v.strip()
    return extra


def _execute_cycle(
    *,
    strategy: str,
    sector: str | None,
    universe: str | None,
    rebalance: str,
    lookback_days: int,
    min_order: float,
    extra_params: dict,
    dry_run: bool,
    state_key: str,
) -> None:
    """리밸런싱 한 사이클을 실행한다. run 커맨드와 schedule 커맨드가 공유한다."""
    tickers = [t.strip() for t in universe.split(",")] if universe else None
    resolved = resolve_universe(universe=tickers, sector=sector)

    strategy_instance = get_strategy(strategy)

    try:
        broker = get_broker()
    except KeyError:
        console.print("[red]오류:[/red] madcamp-week4/.env 파일에 ALPACA_API_KEY_ID, ALPACA_API_SECRET_KEY를 설정하세요.")
        raise typer.Exit(1)

    if tickers:
        universe_label = f"직접 지정 ({len(resolved)}개)"
    elif sector:
        universe_label = f"{sector_display_name(sector)} 섹터 ({len(resolved)}개)"
    else:
        universe_label = f"S&P 500 전체 ({len(resolved)}개)"

    # 상태 파일에서 마지막 리밸런싱 날짜 로드
    last_dt = get_last_rebalance(state_key)

    console.print(f"\n[bold]자동매매 실행[/bold]  ({'dry-run' if dry_run else '[red]실제 주문[/red]'})")
    console.print(f"  전략    : {strategy}")
    console.print(f"  유니버스: {universe_label}")
    console.print(f"  주기    : {rebalance}")
    console.print(f"  오늘    : {date.today()}")
    console.print(f"  마지막 리밸런싱: {last_dt or '(없음 — 즉시 실행)'}")
    console.print()

    try:
        if not broker.is_market_open():
            console.print("[yellow]주의:[/yellow] 현재 시장이 닫혀 있습니다. 주문은 다음 개장 시 체결됩니다.\n")
    except Exception:
        pass

    ctx = StrategyContext(params=extra_params)

    result = run_live(
        strategy=strategy_instance,
        data_provider=get_data_provider(),
        broker=broker,
        ctx=ctx,
        universe=resolved,
        rebalance_freq=rebalance,
        lookback_days=lookback_days,
        last_rebalance_date=last_dt,
        min_order_notional=min_order,
        dry_run=dry_run,
    )

    _print_result(result, dry_run=dry_run)

    # 실제 리밸런싱이 발생했으면 상태 저장
    if result.did_rebalance and not dry_run:
        set_last_rebalance(state_key, date.fromisoformat(result.date))
        console.print(f"[dim]상태 저장됨: {result.date}[/dim]")


# ──────────────────────────────────────────────
# sf trade run
# ──────────────────────────────────────────────

@app.command("run")
def trade_run(
    strategy: str = typer.Option(..., "--strategy", "-s", help="전략 이름"),
    sector: Optional[str] = typer.Option(None, "--sector", help=_SECTOR_HELP),
    universe: Optional[str] = typer.Option(None, "--universe", help="티커 직접 지정 (쉼표 구분)"),
    rebalance: str = typer.Option("monthly", "--rebalance", help="리밸런싱 주기 (monthly/weekly/daily)"),
    lookback_days: int = typer.Option(400, "--lookback-days", help="가격 데이터 조회 기간 (일)"),
    min_order: float = typer.Option(1.0, "--min-order", help="최소 주문 금액 (달러)"),
    param: Optional[List[str]] = typer.Option(None, "--param", help="전략 파라미터 key=value"),
    dry_run: bool = typer.Option(True, "--dry-run/--execute", help="주문 계산만 하거나 실제 제출"),
) -> None:
    """자동매매 한 사이클을 실행한다.

    마지막 리밸런싱 날짜는 ~/.sf/state.json에 자동 저장·로드된다.
    --execute 플래그를 붙여야 실제 주문이 제출된다.
    """
    try:
        extra_params = _parse_params(param)
    except ValueError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(1)

    universe_spec = sector or universe or "sp500"
    state_key = make_state_key(strategy, universe_spec, rebalance)

    try:
        _execute_cycle(
            strategy=strategy,
            sector=sector,
            universe=universe,
            rebalance=rebalance,
            lookback_days=lookback_days,
            min_order=min_order,
            extra_params=extra_params,
            dry_run=dry_run,
            state_key=state_key,
        )
    except Exception as e:
        console.print(f"[red]실행 실패:[/red] {e}")
        raise typer.Exit(1)


# ──────────────────────────────────────────────
# sf trade schedule
# ──────────────────────────────────────────────

@app.command("schedule")
def trade_schedule(
    strategy: str = typer.Option(..., "--strategy", "-s", help="전략 이름"),
    sector: Optional[str] = typer.Option(None, "--sector", help=_SECTOR_HELP),
    universe: Optional[str] = typer.Option(None, "--universe", help="티커 직접 지정 (쉼표 구분)"),
    rebalance: str = typer.Option("monthly", "--rebalance", help="리밸런싱 주기 (monthly/weekly/daily)"),
    lookback_days: int = typer.Option(400, "--lookback-days", help="가격 데이터 조회 기간 (일)"),
    min_order: float = typer.Option(1.0, "--min-order", help="최소 주문 금액 (달러)"),
    param: Optional[List[str]] = typer.Option(None, "--param", help="전략 파라미터 key=value"),
) -> None:
    """주기에 맞춰 자동매매를 반복 실행한다 (프로세스가 살아있는 동안).

    항상 --execute 모드로 실행된다. 서버나 VPS에서 장기 실행용.
    컴퓨터가 꺼져도 동작하게 하려면 GitHub Actions 또는 systemd 서비스를 사용한다.
    (cli/README.md 참고)
    """
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
    except ImportError:
        console.print("[red]오류:[/red] apscheduler가 설치되지 않았습니다: pip install 'apscheduler>=3.10,<4'")
        raise typer.Exit(1)

    if rebalance not in _CRON_ARGS:
        console.print(f"[red]오류:[/red] rebalance는 monthly/weekly/daily 중 하나여야 합니다.")
        raise typer.Exit(1)

    try:
        extra_params = _parse_params(param)
    except ValueError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(1)

    universe_spec = sector or universe or "sp500"
    state_key = make_state_key(strategy, universe_spec, rebalance)
    cron_kwargs = _CRON_ARGS[rebalance]

    def _job() -> None:
        try:
            _execute_cycle(
                strategy=strategy,
                sector=sector,
                universe=universe,
                rebalance=rebalance,
                lookback_days=lookback_days,
                min_order=min_order,
                extra_params=extra_params,
                dry_run=False,
                state_key=state_key,
            )
        except Exception as e:
            console.print(f"[red]사이클 오류 (계속 실행됨):[/red] {e}")

    scheduler = BlockingScheduler(timezone="America/New_York")
    scheduler.add_job(_job, "cron", **cron_kwargs)

    next_run = scheduler.get_jobs()[0].next_run_time
    console.print(f"\n[bold]자동매매 스케줄러 시작[/bold]")
    console.print(f"  전략  : {strategy}")
    console.print(f"  주기  : {rebalance}  ({cron_kwargs})")
    console.print(f"  다음 실행: {next_run}")
    console.print("  [dim]Ctrl+C로 중단[/dim]\n")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        console.print("\n스케줄러 중단됨.")


# ──────────────────────────────────────────────
# 출력 헬퍼
# ──────────────────────────────────────────────

def _print_result(result, dry_run: bool) -> None:
    status = "[green]리밸런싱 실행됨[/green]" if result.did_rebalance else "[dim]리밸런싱 건너뜀[/dim]"
    console.print(f"상태   : {status}")
    if result.skipped_reason:
        console.print(f"사유   : {result.skipped_reason}")
    console.print(f"총 자산: ${result.equity:,.2f}")
    console.print()

    if result.current_positions:
        pos_table = Table(title="현재 포지션", show_lines=True)
        pos_table.add_column("종목", style="cyan")
        pos_table.add_column("수량", justify="right")
        pos_table.add_column("시장가치", justify="right")
        pos_table.add_column("비중", justify="right", style="dim")
        equity = result.equity or 1.0
        for p in sorted(result.current_positions, key=lambda x: -x.market_value):
            weight_pct = p.market_value / equity * 100
            pos_table.add_row(p.symbol, f"{p.qty:.4f}", f"${p.market_value:,.2f}", f"{weight_pct:.1f}%")
        console.print(pos_table)
        console.print()

    if result.orders:
        label = "생성된 주문 (dry-run)" if dry_run else "실행된 주문"
        ord_table = Table(title=label, show_lines=True)
        ord_table.add_column("종목", style="cyan")
        ord_table.add_column("방향", justify="center")
        ord_table.add_column("금액", justify="right")
        for o in result.orders:
            side_str = "[green]매수[/green]" if o.side == "buy" else "[red]매도[/red]"
            ord_table.add_row(o.symbol, side_str, f"${o.notional:,.2f}")
        console.print(ord_table)
    elif result.did_rebalance:
        console.print("[dim]변경 사항 없음 (모든 종목이 목표 비중 이내)[/dim]")
