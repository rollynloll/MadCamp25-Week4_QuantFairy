from __future__ import annotations

import contextlib
import io

import pandas as pd


class YFinanceProvider:
    """DataProvider backed by yfinance. Default for CLI and local development."""

    def get_prices(self, tickers: list[str], start: str, end: str) -> pd.DataFrame:
        import yfinance as yf

        if not tickers:
            return pd.DataFrame()

        # yfinance가 timezone 파싱 실패 등의 경고를 stderr에 직접 출력한다.
        # runner가 이미 누락 심볼을 gracefully 처리하므로 노이즈만 억제한다.
        with contextlib.redirect_stderr(io.StringIO()):
            raw = yf.download(
                tickers,
                start=start,
                end=end,
                auto_adjust=True,
                progress=False,
                threads=True,
            )

        if raw.empty:
            return pd.DataFrame()

        # yfinance는 여러 티커면 MultiIndex 컬럼, 단일 티커면 단일 레벨 컬럼을 반환한다.
        if isinstance(raw.columns, pd.MultiIndex):
            df = raw["Close"]
        else:
            df = raw[["Close"]].rename(columns={"Close": tickers[0]})

        df.index = pd.to_datetime(df.index)
        df.index.name = "date"
        df.columns.name = None
        return df.sort_index()
