from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from cli.bots import BotConfig, load_bots_config, validate_bots_config
from cli.container import get_broker, get_data_provider
from cli.state import (
    get_bot_last_rebalance,
    is_bot_stopped,
    mark_bot_running,
    set_bot_last_rebalance,
)
from engine.data.universe import resolve_universe_preset
from engine.strategies.base import StrategyContext
from engine.strategies.registry import get_strategy
from engine.trading.market_hours import is_within_market_hours
from engine.trading.scheduler import run_live

console = Console()


def run_bots(
    bot: Optional[str] = typer.Option(None, "--bot", help="특정 봇 이름"),
    all_bots: bool = typer.Option(False, "--all", help="전체 봇 순차 실행"),
    dry_run: bool = typer.Option(False, "--dry-run", help="주문 미리보기만 (실제 실행 없음)"),
    config: str = typer.Option("config/bots.yaml", "--config", help="bots.yaml 경로"),
) -> None:
    """봇 리밸런싱을 실행한다. --bot <name> 또는 --all 중 하나를 지정해야 한다."""

    if not bot and not all_bots:
        console.print("[red]오류:[/red] --bot <name> 또는 --all 중 하나를 지정해야 합니다.")
        raise typer.Exit(1)

    config_path = Path(config)
    try:
        cfg = load_bots_config(config_path)
        validate_bots_config(cfg)
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(1)

    bots_to_run = cfg.bots if all_bots else [b for b in cfg.bots if b.name == bot]
    if not bots_to_run:
        console.print(f"[red]오류:[/red] 봇을 찾을 수 없습니다: {bot!r}")
        raise typer.Exit(1)

    try:
        broker = get_broker()
        account = broker.get_account()
    except KeyError:
        console.print(
            "[red]오류:[/red] .env에 ALPACA_API_KEY_ID, ALPACA_API_SECRET_KEY를 설정하세요."
        )
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]브로커 연결 실패:[/red] {e}")
        raise typer.Exit(1)

    mode_label = "dry-run" if dry_run else "[red]실제 주문[/red]"
    console.print(f"\n[bold]자동매매 실행[/bold]  ({mode_label})")
    console.print(f"  총 자산 : [bold]${account.equity:,.2f}[/bold]")
    console.print(f"  현금    : ${account.cash:,.2f}")
    console.print(f"  봇 수   : {len(bots_to_run)}개")
    console.print()

    if not is_within_market_hours():
        console.print(
            "[yellow]주의:[/yellow] 현재 미국 시장이 닫혀 있습니다. "
            "주문은 다음 개장 시 체결됩니다.\n"
        )

    for bot_cfg in bots_to_run:
        if is_bot_stopped(bot_cfg.name) and not dry_run:
            console.print(f"  [dim]{bot_cfg.name}: 중지됨 — sf stop 해제 후 실행 가능[/dim]")
            continue
        _run_single_bot(bot_cfg, account.equity, broker, dry_run)


def _run_single_bot(
    bot_cfg: BotConfig,
    total_equity: float,
    broker,
    dry_run: bool,
) -> None:
    console.print(f"[bold cyan]── 봇: {bot_cfg.name}[/bold cyan]")
    console.print(
        f"   전략: {bot_cfg.strategy}  유니버스: {bot_cfg.universe}  "
        f"주기: {bot_cfg.rebalance}  자본: {bot_cfg.capital_pct*100:.0f}%"
    )

    try:
        universe = resolve_universe_preset(bot_cfg.universe)
        strategy = get_strategy(bot_cfg.strategy)
    except (ValueError, KeyError) as e:
        console.print(f"   [red]초기화 실패:[/red] {e}")
        return

    ctx = StrategyContext(params=bot_cfg.params)
    last_dt = get_bot_last_rebalance(bot_cfg.name)

    try:
        result = run_live(
            strategy=strategy,
            data_provider=get_data_provider(),
            broker=broker,
            ctx=ctx,
            universe=universe,
            rebalance_freq=bot_cfg.rebalance,
            last_rebalance_date=last_dt,
            capital_pct=bot_cfg.capital_pct,
            dry_run=dry_run,
        )
    except Exception as e:
        console.print(f"   [red]실행 실패:[/red] {e}\n")
        return

    if not result.did_rebalance:
        console.print(f"   [dim]건너뜀: {result.skipped_reason}[/dim]\n")
        return

    if result.orders:
        sells = [o for o in result.orders if o.side == "sell"]
        buys = [o for o in result.orders if o.side == "buy"]
        t = Table(show_lines=False, box=None, padding=(0, 1))
        t.add_column("방향", style="bold", width=4)
        t.add_column("종목", style="cyan")
        t.add_column("금액", justify="right")
        for o in sells:
            t.add_row("[red]매도[/red]", o.symbol, f"${o.notional:,.0f}")
        for o in buys:
            t.add_row("[green]매수[/green]", o.symbol, f"${o.notional:,.0f}")
        console.print(t)
    else:
        console.print("   [dim]변경 없음 (목표 비중 이내)[/dim]")

    action = "dry-run 완료" if dry_run else "주문 제출 완료"
    console.print(f"   {action}  자산: ${result.equity:,.2f}\n")

    if result.did_rebalance and not dry_run:
        set_bot_last_rebalance(bot_cfg.name, date.fromisoformat(result.date))
        mark_bot_running(bot_cfg.name)
