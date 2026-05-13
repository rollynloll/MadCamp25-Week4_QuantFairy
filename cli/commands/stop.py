from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from cli.bots import load_bots_config
from cli.container import get_broker
from cli.state import is_bot_stopped, mark_bot_running, mark_bot_stopped
from engine.trading.order import Order

console = Console()


def stop_bot(
    bot: Optional[str] = typer.Option(None, "--bot", help="중지할 봇 이름"),
    all_bots: bool = typer.Option(False, "--all", help="전체 봇 중지"),
    liquidate: bool = typer.Option(False, "--liquidate", help="포지션 전량 청산"),
    resume: bool = typer.Option(False, "--resume", help="중지된 봇을 재개"),
    config: str = typer.Option("config/bots.yaml", "--config", help="bots.yaml 경로"),
) -> None:
    """봇을 중지하거나 재개한다. --liquidate로 전체 포지션 청산."""

    if not bot and not all_bots:
        console.print("[red]오류:[/red] --bot <name> 또는 --all 중 하나를 지정해야 합니다.")
        raise typer.Exit(1)

    config_path = Path(config)
    try:
        cfg = load_bots_config(config_path)
    except FileNotFoundError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(1)

    bots_to_stop = cfg.bots if all_bots else [b for b in cfg.bots if b.name == bot]
    if not bots_to_stop:
        console.print(f"[red]오류:[/red] 봇을 찾을 수 없습니다: {bot!r}")
        raise typer.Exit(1)

    if liquidate:
        console.print("\n[bold red]전체 포지션 청산[/bold red]")
        typer.confirm("정말로 모든 포지션을 청산하시겠습니까?", abort=True)
        _liquidate_all()

    for b in bots_to_stop:
        if resume:
            mark_bot_running(b.name)
            console.print(f"  [green]재개됨:[/green] {b.name}")
        else:
            mark_bot_stopped(b.name)
            status = "이미 중지됨" if is_bot_stopped(b.name) else "중지됨"
            console.print(f"  [yellow]중지됨:[/yellow] {b.name}")

    action = "재개" if resume else "중지"
    console.print(f"\n총 {len(bots_to_stop)}개 봇 {action} 완료.")


def _liquidate_all() -> None:
    """미체결 주문 취소 후 전체 포지션 시장가 매도."""
    try:
        broker = get_broker()
    except Exception as e:
        console.print(f"[red]브로커 연결 실패:[/red] {e}")
        raise typer.Exit(1)

    try:
        broker.cancel_all_orders()
        console.print("  미체결 주문 취소 완료")
    except Exception as e:
        console.print(f"  [yellow]주문 취소 실패 (계속 진행):[/yellow] {e}")

    positions = broker.get_positions()
    if not positions:
        console.print("  보유 포지션 없음")
        return

    orders = [
        Order(symbol=p.symbol, side="sell", notional=p.market_value)
        for p in positions
    ]
    broker.place_orders(orders)
    console.print(f"  {len(orders)}개 종목 청산 주문 제출 완료")
