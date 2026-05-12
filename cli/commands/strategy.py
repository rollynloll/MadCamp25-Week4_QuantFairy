from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from engine.strategies.registry import get_strategy, list_entrypoints

app = typer.Typer(help="전략 목록 조회 및 상세 정보")
console = Console()


@app.command("list")
def strategy_list() -> None:
    """등록된 전략 목록을 출력한다."""
    table = Table(title="등록된 전략 목록", show_lines=True)
    table.add_column("Entrypoint", style="cyan", no_wrap=True)
    table.add_column("이름", style="white")

    for ep in list_entrypoints():
        try:
            instance = get_strategy(ep)
            name = getattr(instance, "name", "-")
        except Exception:
            name = "-"
        table.add_row(ep, name)

    console.print(table)


@app.command("show")
def strategy_show(entrypoint: str = typer.Argument(..., help="전략 entrypoint")) -> None:
    """전략의 이름과 기본 파라미터를 출력한다."""
    try:
        instance = get_strategy(entrypoint)
    except ValueError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(1)

    name = getattr(instance, "name", entrypoint)
    console.print(f"\n[bold cyan]{name}[/bold cyan]")
    console.print(f"Entrypoint: {entrypoint}")

    # 기본 파라미터가 정의된 경우 테이블로 출력
    defaults = getattr(instance, "default_params", None)
    if defaults:
        table = Table(title="기본 파라미터", show_lines=True)
        table.add_column("파라미터", style="cyan")
        table.add_column("기본값", style="white")
        for k, v in defaults.items():
            table.add_row(k, str(v))
        console.print(table)
