from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from cli.container import get_broker

app = typer.Typer(help="계좌 및 포지션 조회")
console = Console()


def _make_broker():
    try:
        return get_broker()
    except KeyError as e:
        console.print(f"[red]오류:[/red] 환경변수 {e}가 설정되지 않았습니다.")
        console.print("  madcamp-week4/.env 파일에 ALPACA_API_KEY_ID, ALPACA_API_SECRET_KEY를 설정하세요.")
        raise typer.Exit(1)


@app.command("show")
def account_show() -> None:
    """계좌 요약 정보를 출력한다 (자산, 현금, 매수 가능 금액)."""
    broker = _make_broker()
    try:
        account = broker.get_account()
        is_open = broker.is_market_open()
    except Exception as e:
        console.print(f"[red]조회 실패:[/red] {e}")
        raise typer.Exit(1)

    market_status = "[green]개장[/green]" if is_open else "[red]휴장[/red]"

    table = Table(title="계좌 요약", show_lines=True)
    table.add_column("항목", style="cyan", no_wrap=True)
    table.add_column("금액", style="white", justify="right")

    table.add_row("총 자산 (Equity)",      f"${account.equity:>12,.2f}")
    table.add_row("포지션 시장가치",        f"${account.portfolio_value:>12,.2f}")
    table.add_row("현금 잔고",             f"${account.cash:>12,.2f}")
    table.add_row("매수 가능 금액",         f"${account.buying_power:>12,.2f}")
    table.add_row("통화",                  account.currency)
    table.add_row("시장 상태",             market_status)

    console.print()
    console.print(table)


@app.command("positions")
def account_positions() -> None:
    """현재 보유 포지션 상세 목록을 출력한다."""
    broker = _make_broker()
    try:
        positions = broker.get_positions()
        account = broker.get_account()
    except Exception as e:
        console.print(f"[red]조회 실패:[/red] {e}")
        raise typer.Exit(1)

    if not positions:
        console.print("\n[dim]보유 포지션 없음[/dim]")
        return

    # 시장가치 내림차순 정렬
    positions = sorted(positions, key=lambda p: -p.market_value)
    equity = account.equity or 1.0

    table = Table(
        title=f"보유 포지션 ({len(positions)}개 / 총 자산 ${equity:,.2f})",
        show_lines=True,
    )
    table.add_column("종목",        style="cyan",   no_wrap=True)
    table.add_column("수량",        justify="right")
    table.add_column("평균 단가",   justify="right")
    table.add_column("시장가치",    justify="right")
    table.add_column("비중",        justify="right", style="dim")
    table.add_column("미실현 손익", justify="right")
    table.add_column("손익률",      justify="right")

    for p in positions:
        weight_pct = p.market_value / equity * 100
        pnl_color = "green" if p.unrealized_pnl >= 0 else "red"
        pnl_sign = "+" if p.unrealized_pnl >= 0 else ""
        pnl_pct_sign = "+" if p.unrealized_pnl_pct >= 0 else ""

        table.add_row(
            p.symbol,
            f"{p.qty:.4f}",
            f"${p.avg_entry_price:,.2f}",
            f"${p.market_value:,.2f}",
            f"{weight_pct:.1f}%",
            f"[{pnl_color}]{pnl_sign}${p.unrealized_pnl:,.2f}[/{pnl_color}]",
            f"[{pnl_color}]{pnl_pct_sign}{p.unrealized_pnl_pct * 100:.2f}%[/{pnl_color}]",
        )

    console.print()
    console.print(table)
