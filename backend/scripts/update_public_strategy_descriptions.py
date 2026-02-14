import asyncio
import os
import pathlib
import sys
from datetime import datetime, timezone

import asyncpg
from dotenv import load_dotenv


STRATEGY_UPDATES = {
    "momentum_top10_12m_v1": {
        "one_liner": "Top-N by 12M return, monthly rebalance",
        "one_liner_ko": "12개월 수익률 상위 N개를 매수하고 월간 리밸런싱",
        "full_description": (
            "This strategy ranks the universe by 12-month total return and buys the top N names. "
            "It rebalances monthly and equal-weights positions, replacing laggards with new leaders. "
            "It is designed for diversified large-cap universes and can be vulnerable during sharp momentum reversals."
        ),
        "full_description_ko": (
            "이 전략은 12개월 누적 수익률로 종목을 순위화해 상위 N개를 매수합니다. "
            "매달 리밸런싱하며 동일 비중으로 보유하고, 성과가 떨어진 종목은 새로운 상위 종목으로 교체합니다. "
            "대형주 분산 유니버스에 적합하지만 모멘텀 급반전 구간에서는 손실이 커질 수 있습니다."
        ),
        "thesis": (
            "Persistent relative strength can be harvested by periodically rotating into recent winners while keeping turnover manageable."
        ),
        "thesis_ko": "최근 강세 종목의 상대적 강도를 활용하되, 월 단위 교체로 과도한 회전율을 줄입니다.",
    },
    "trend_sma200_v1": {
        "one_liner": "Risk-on above 200D SMA, else cash",
        "one_liner_ko": "벤치마크가 200일 이동평균 위이면 위험자산, 아래면 현금",
        "full_description": (
            "A simple trend filter on the benchmark: if price is above the 200-day moving average, "
            "the strategy stays invested; if below, it shifts to cash. The signal is checked daily "
            "to reduce drawdowns in prolonged bear markets. It can underperform in sideways markets due to whipsaws."
        ),
        "full_description_ko": (
            "벤치마크가 200일 이동평균 위에 있으면 위험자산을 보유하고, 아래로 내려가면 현금으로 전환하는 단순 추세 필터입니다. "
            "일별로 신호를 확인해 하락장 손실을 줄이는 데 도움이 될 수 있습니다. "
            "횡보장에서는 잦은 신호 전환으로 성과가 약해질 수 있습니다."
        ),
        "thesis": "Long-term moving averages help separate trending regimes from risk-off periods.",
        "thesis_ko": "장기 이동평균을 통해 추세 구간과 위험 구간을 구분합니다.",
    },
    "rsi_mean_reversion_v1": {
        "one_liner": "Buy RSI < 30, exit RSI > 50",
        "one_liner_ko": "RSI가 30 아래면 매수, 50 위면 청산",
        "full_description": (
            "This mean reversion strategy uses RSI on a single benchmark (default SPY). "
            "It buys when RSI falls below the entry threshold and exits when RSI rebounds above the exit level. "
            "It tends to work best in range-bound markets and can struggle during strong trends."
        ),
        "full_description_ko": (
            "단일 벤치마크(기본 SPY)에 RSI를 적용하는 평균회귀 전략입니다. "
            "RSI가 진입 기준 아래로 내려가면 매수하고, 반등해 종료 기준을 넘으면 매도합니다. "
            "횡보장에서 유리하지만 강한 추세에서는 손실이 커질 수 있습니다."
        ),
        "thesis": "Short-term oversold conditions often revert toward the mean.",
        "thesis_ko": "단기 과매도 구간은 평균으로 되돌아갈 가능성이 높습니다.",
    },
    "low_volatility_v1": {
        "one_liner": "Select low-volatility assets, monthly rebalance",
        "one_liner_ko": "변동성이 낮은 종목을 선별해 월간 리밸런싱",
        "full_description": (
            "Selects the lowest-volatility assets over a lookback window and allocates either equal or inverse-vol weights. "
            "It rebalances monthly to keep a defensive tilt and a smoother equity curve. "
            "It may lag during sharp bull runs but can help reduce drawdowns."
        ),
        "full_description_ko": (
            "과거 변동성이 낮은 자산을 선별해 동일 비중 또는 변동성 역가중으로 배분합니다. "
            "매달 리밸런싱하며 방어적 성향과 완만한 수익 곡선을 목표로 합니다. "
            "강한 상승장에서는 뒤처질 수 있지만 낙폭을 줄이는 데 도움이 됩니다."
        ),
        "thesis": "Lower volatility assets can deliver steadier risk-adjusted returns.",
        "thesis_ko": "낮은 변동성 자산은 더 안정적인 위험조정 수익을 제공할 수 있습니다.",
    },
    "vol_adj_momentum_v1": {
        "one_liner": "Rank by return/volatility, monthly rebalance",
        "one_liner_ko": "수익/변동성 점수로 랭킹, 월간 리밸런싱",
        "full_description": (
            "Ranks assets by return divided by volatility to favor strong yet stable trends. "
            "By penalizing high volatility, it aims to avoid fragile momentum names while still following winners. "
            "Rebalanced monthly; still exposed to momentum crashes and regime shifts."
        ),
        "full_description_ko": (
            "수익률을 변동성으로 나눈 점수로 종목을 순위화해, 강하지만 안정적인 추세를 선호합니다. "
            "높은 변동성을 패널티로 주어 취약한 모멘텀 종목을 피하려고 합니다. "
            "월간 리밸런싱이며 모멘텀 붕괴나 레짐 전환에는 여전히 취약할 수 있습니다."
        ),
        "thesis": "Adjusting momentum by volatility balances return potential and risk.",
        "thesis_ko": "변동성으로 보정한 모멘텀은 수익과 위험의 균형을 개선합니다.",
    },
    "risk_on_off_v1": {
        "one_liner": "Rotate to cash when benchmark falls below SMA",
        "one_liner_ko": "벤치마크가 SMA 아래면 현금, 위면 위험자산 바스켓",
        "full_description": (
            "Combines a regime filter with a ranked basket. When the benchmark is above its SMA, "
            "the strategy holds the top-K risk assets; when it falls below, it rotates to cash. "
            "This can reduce large drawdowns but may whipsaw in sideways markets."
        ),
        "full_description_ko": (
            "레짐 필터와 랭킹 바스켓을 결합한 전략입니다. 벤치마크가 SMA 위에 있으면 상위 K개 위험자산을 보유하고, "
            "아래로 내려가면 현금으로 전환합니다. 큰 낙폭을 줄이는 데 도움이 될 수 있지만 횡보장에서는 흔들림이 생길 수 있습니다."
        ),
        "thesis": "A simple regime filter helps stay invested in uptrends and step aside in downtrends.",
        "thesis_ko": "레짐 필터로 상승장에는 참여하고 하락장에는 비중을 줄입니다.",
    },
}

LEGACY_FULL_DESCRIPTION = {
    "momentum_top10_12m_v1": "Cross-sectional momentum using 12M returns.",
    "trend_sma200_v1": "Simple trend following on SMA200.",
    "rsi_mean_reversion_v1": "RSI mean reversion strategy.",
    "low_volatility_v1": "Low volatility selection with inverse-vol or equal weighting.",
    "vol_adj_momentum_v1": "Momentum ranked by return/volatility to reduce crash risk.",
    "risk_on_off_v1": "Risk-on basket when benchmark above SMA, otherwise cash.",
}

LEGACY_THESIS = {
    "momentum_top10_12m_v1": "Buy top performers and rebalance monthly.",
    "trend_sma200_v1": "Risk-on when above SMA200, else cash.",
    "rsi_mean_reversion_v1": "Buy oversold, exit on mean reversion.",
    "low_volatility_v1": "Lower vol assets tend to defend in drawdowns.",
    "vol_adj_momentum_v1": "Risk-adjusted momentum improves robustness.",
    "risk_on_off_v1": "Regime filter reduces large drawdowns.",
}


def _is_blank(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def _contains_korean(text: str) -> bool:
    if not isinstance(text, str):
        return False
    return any("\uac00" <= ch <= "\ud7a3" for ch in text)


def normalize_dsn(dsn: str) -> str:
    if dsn.startswith("postgresql+asyncpg://"):
        return "postgresql://" + dsn[len("postgresql+asyncpg://") :]
    if dsn.startswith("postgres+asyncpg://"):
        return "postgresql://" + dsn[len("postgres+asyncpg://") :]
    return dsn


async def main() -> None:
    env_path = pathlib.Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        print("DATABASE_URL is not set", file=sys.stderr)
        sys.exit(1)

    dsn = normalize_dsn(dsn)
    conn = await asyncpg.connect(dsn)
    try:
        force = "--force" in sys.argv
        await conn.execute(
            """
            ALTER TABLE public_strategies
              ADD COLUMN IF NOT EXISTS one_liner_ko text,
              ADD COLUMN IF NOT EXISTS full_description_ko text,
              ADD COLUMN IF NOT EXISTS thesis_ko text
            """
        )
        now = datetime.now(timezone.utc)
        for strategy_id, payload in STRATEGY_UPDATES.items():
            row = await conn.fetchrow(
                """
                SELECT one_liner, one_liner_ko, full_description, full_description_ko, thesis, thesis_ko
                FROM public_strategies
                WHERE public_strategy_id = $1
                """,
                strategy_id,
            )
            if not row:
                print(f"[skip] {strategy_id}: not found")
                continue

            update = {}
            if (
                force
                or _is_blank(row["one_liner"])
                or _contains_korean(row["one_liner"])
                or (row["one_liner_ko"] and row["one_liner"] == row["one_liner_ko"])
            ):
                update["one_liner"] = payload["one_liner"]

            if force or _is_blank(row["one_liner_ko"]) or not _contains_korean(row["one_liner_ko"]):
                update["one_liner_ko"] = payload["one_liner_ko"]

            legacy_full = LEGACY_FULL_DESCRIPTION.get(strategy_id)
            if (
                force
                or _is_blank(row["full_description"])
                or _contains_korean(row["full_description"])
                or (row["full_description_ko"] and row["full_description"] == row["full_description_ko"])
                or (legacy_full and row["full_description"] == legacy_full)
            ):
                update["full_description"] = payload["full_description"]

            if force or _is_blank(row["full_description_ko"]) or not _contains_korean(row["full_description_ko"]):
                update["full_description_ko"] = payload["full_description_ko"]

            legacy_thesis = LEGACY_THESIS.get(strategy_id)
            if (
                force
                or _is_blank(row["thesis"])
                or _contains_korean(row["thesis"])
                or (row["thesis_ko"] and row["thesis"] == row["thesis_ko"])
                or (legacy_thesis and row["thesis"] == legacy_thesis)
            ):
                update["thesis"] = payload["thesis"]

            if force or _is_blank(row["thesis_ko"]) or not _contains_korean(row["thesis_ko"]):
                update["thesis_ko"] = payload["thesis_ko"]

            if not update:
                print(f"[skip] {strategy_id}: already up to date")
                continue

            update["updated_at"] = now
            cols = list(update.keys())
            set_clause = ", ".join(f"{col} = ${i + 2}" for i, col in enumerate(cols))
            values = [update[col] for col in cols]
            await conn.execute(
                f"UPDATE public_strategies SET {set_clause} WHERE public_strategy_id = $1",
                strategy_id,
                *values,
            )
            print(f"[updated] {strategy_id}: {', '.join(cols)}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
