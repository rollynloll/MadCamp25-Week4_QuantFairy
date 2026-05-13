from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from cli.bots import load_bots_config
from cli.container import get_broker
from cli.state import get_bot_last_rebalance, is_bot_stopped

console = Console()


def show_status(
    config: str = typer.Option("config/bots.yaml", "--config", help="bots.yaml 경로"),
) -> None:
    """전략별 포지션·잔고·마지막 실행·다음 실행 일정을 출력한다."""

    config_path = Path(config)
    try:
        cfg = load_bots_config(config_path)
    except FileNotFoundError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(1)

    try:
        broker = get_broker()
        account = broker.get_account()
        positions = broker.get_positions()
    except Exception as e:
        console.print(f"[red]브로커 연결 실패:[/red] {e}")
        raise typer.Exit(1)

    console.print(
        f"\n[bold]계좌 요약[/bold]  총자산 [bold]${account.equity:,.2f}[/bold]  "
        f"현금 ${account.cash:,.2f}  매수여력 ${account.buying_power:,.2f}\n"
    )

    # 봇 상태 테이블
    bot_table = Table(title="봇 상태", show_lines=True)
    bot_table.add_column("봇", style="cyan")
    bot_table.add_column("전략")
    bot_table.add_column("유니버스")
    bot_table.add_column("주기")
    bot_table.add_column("자본%", justify="right")
    bot_table.add_column("자본($)", justify="right")
    bot_table.add_column("마지막 실행", justify="center")
    bot_table.add_column("다음 실행", justify="center")
    bot_table.add_column("상태", justify="center")

    for bot in cfg.bots:
        last_dt = get_bot_last_rebalance(bot.name)
        stopped = is_bot_stopped(bot.name)
        capital = account.equity * bot.capital_pct
        next_dt = _next_rebalance(bot.rebalance, last_dt)

        today = date.today()
        if next_dt and next_dt <= today and not stopped:
            next_str = f"[yellow]{next_dt}[/yellow]"
        else:
            next_str = str(next_dt) if next_dt else "-"

        status_str = "[red]중지됨[/red]" if stopped else "[green]실행중[/green]"

        bot_table.add_row(
            bot.name,
            bot.strategy,
            bot.universe,
            bot.rebalance,
            f"{bot.capital_pct * 100:.0f}%",
            f"${capital:,.0f}",
            str(last_dt) if last_dt else "[dim]-[/dim]",
            next_str,
            status_str,
        )

    console.print(bot_table)

    # 현재 포지션 테이블
    if positions:
        pos_table = Table(title="현재 포지션", show_lines=True)
        pos_table.add_column("종목", style="cyan")
        pos_table.add_column("수량", justify="right")
        pos_table.add_column("시장가치($)", justify="right")
        pos_table.add_column("비중", justify="right")
        pos_table.add_column("미실현 손익", justify="right")

        for p in sorted(positions, key=lambda x: -x.market_value):
            weight_pct = p.market_value / account.equity * 100
            pnl_color = "green" if p.unrealized_pnl >= 0 else "red"
            pnl_str = f"[{pnl_color}]${p.unrealized_pnl:+,.0f} ({p.unrealized_pnl_pct*100:+.1f}%)[/{pnl_color}]"
            pos_table.add_row(
                p.symbol,
                f"{p.qty:.4f}",
                f"${p.market_value:,.2f}",
                f"{weight_pct:.1f}%",
                pnl_str,
            )
        console.print()
        console.print(pos_table)
    else:
        console.print("\n[dim]보유 포지션 없음[/dim]")


def _next_rebalance(freq: str, last_dt: Optional[date]) -> Optional[date]:
    """마지막 리밸런싱 날짜로부터 다음 실행 예정일을 계산한다."""
    today = date.today()
    if last_dt is None:
        return today

    if freq == "daily":
        d = last_dt + timedelta(days=1)
        while d.weekday() >= 5:
            d += timedelta(days=1)
        return d

    if freq == "weekly":
        days = (7 - last_dt.weekday()) % 7 or 7
        return last_dt + timedelta(days=days)

    if freq == "monthly":
        if last_dt.month == 12:
            return date(last_dt.year + 1, 1, 1)
        return date(last_dt.year, last_dt.month + 1, 1)

    return None
