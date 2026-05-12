from __future__ import annotations

from typing import Protocol

import pandas as pd


# DataProvider는 가격 데이터 소스의 공통 인터페이스(Protocol)다.
# Protocol을 사용하므로 명시적으로 상속하지 않아도 get_prices 메서드만 구현하면
# 타입 체커가 DataProvider로 인정한다 (duck typing의 정적 버전).
#
# 구현체 예시:
#   - infra/data/yfinance.py  → YFinanceProvider  (CLI, 로컬 개발용)
#   - infra/data/db.py        → DBProvider        (웹 백엔드, DB에 데이터 수집 후 사용)
#
# engine/ 내부는 이 인터페이스만 알고, 실제 구현체가 무엇인지 모른다.
# 의존성은 외부(CLI entrypoint, FastAPI startup)에서 주입된다.
class DataProvider(Protocol):
    def get_prices(
        self,
        tickers: list[str],
        start: str,
        end: str,
    ) -> pd.DataFrame:
        # tickers : 가격 데이터를 요청할 심볼 목록 (예: ["AAPL", "MSFT", "SPY"])
        # start   : 조회 시작일, ISO 형식 문자열 (예: "2020-01-01")
        # end     : 조회 종료일, ISO 형식 문자열 (예: "2024-12-31")
        #
        # 반환값 형식:
        #   - index  : pd.DatetimeIndex (거래일만 포함, 주말/공휴일 제외)
        #   - columns: tickers (심볼명)
        #   - values : adj_close 수정 종가 (float)
        #   - 데이터가 없는 날짜/심볼은 NaN으로 채워진다
        #
        # 예시:
        #          AAPL    MSFT    SPY
        # 2023-01-03  130.28  239.58  382.05
        # 2023-01-04  134.00  241.00  385.00
        # ...
        ...
