from __future__ import annotations

from pathlib import Path

import typer
from dotenv import load_dotenv

_ROOT = Path(__file__).parents[1]
load_dotenv(_ROOT / ".env", override=False)
load_dotenv(_ROOT / ".env.local", override=True)

from cli.commands.account import app as account_app
from cli.commands.backtest import app as backtest_app
from cli.commands.run import run_bots
from cli.commands.status import show_status
from cli.commands.stop import stop_bot
from cli.commands.strategy import app as strategy_app
from cli.commands.trade import app as trade_app

app = typer.Typer(
    name="sf",
    help="StockFairy — 퀀트 전략 백테스트 + 자동매매 CLI",
    no_args_is_help=True,
)

app.add_typer(strategy_app, name="strategy")
app.add_typer(backtest_app, name="backtest")
app.add_typer(trade_app, name="trade")
app.add_typer(account_app, name="account")

# v2.1 — bots.yaml 기반 다중 봇 커맨드
app.command("run")(run_bots)
app.command("status")(show_status)
app.command("stop")(stop_bot)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
