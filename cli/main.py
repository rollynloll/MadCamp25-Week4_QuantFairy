from __future__ import annotations

from pathlib import Path

import typer
from dotenv import load_dotenv

# 프로젝트 루트(madcamp-week4/)의 .env를 자동 로드한다.
# Alpaca API 키, DEFAULT_USER_ID 등이 여기에 있다.
load_dotenv(Path(__file__).parents[1] / ".env")

from cli.commands.account import app as account_app
from cli.commands.backtest import app as backtest_app
from cli.commands.strategy import app as strategy_app
from cli.commands.trade import app as trade_app

app = typer.Typer(
    name="sf",
    help="StockFairy — 퀀트 전략 백테스트 CLI",
    no_args_is_help=True,
)

app.add_typer(strategy_app, name="strategy")
app.add_typer(backtest_app, name="backtest")
app.add_typer(trade_app, name="trade")
app.add_typer(account_app, name="account")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
