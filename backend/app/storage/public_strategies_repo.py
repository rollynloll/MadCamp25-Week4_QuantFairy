from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.core.config import Settings
from app.core.time import now_kst
from app.storage.supabase_client import get_supabase_client


DEFAULT_PUBLIC_STRATEGIES = [
    {
        "public_strategy_id": "momentum_top10_12m_v1",
        "name": "Momentum Top-10 (12M)",
        "one_liner": "Top-N by 12M return, monthly rebalance",
        "one_liner_ko": "12개월 수익률 상위 N개를 매수하고 월간 리밸런싱",
        "category": "momentum",
        "tags": ["momentum", "cross-sectional"],
        "risk_level": "mid",
        "version": "1.0.0",
        "author_name": "QuantFairy",
        "author_type": "official",
        "sample_metrics": {
            "pnl_amount": 15600.0,
            "pnl_pct": 15.6,
            "sharpe": 1.4,
            "max_drawdown_pct": -4.2,
            "win_rate_pct": 58.2,
        },
        "sample_trade_stats": {"trades_count": 120, "avg_hold_hours": 36},
        "adds_count": 128,
        "likes_count": 64,
        "runs_count": 320,
        "supported_assets": ["US_Equity"],
        "supported_timeframes": ["1D"],
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
        "rules": {
            "signal_definition": "Rank by 12M return.",
            "entry_rules": "Buy top-N.",
            "exit_rules": "Sell on rebalance.",
            "rebalance_rule": "Monthly.",
            "position_sizing": "Equal weight.",
        },
        "param_schema": {
            "type": "object",
            "properties": {
                "lookback_days": {"type": "integer", "minimum": 60, "maximum": 504, "default": 252},
                "top_n": {"type": "integer", "minimum": 5, "maximum": 50, "default": 10},
                "rebalance": {"type": "string", "enum": ["monthly"], "default": "monthly"},
            },
            "required": ["lookback_days", "top_n"],
        },
        "default_params": {"lookback_days": 252, "top_n": 10, "rebalance": "monthly"},
        "recommended_presets": [],
        "requirements": {
            "universe": {"min_symbols": 20, "max_symbols": 500, "supports_custom_tickers": True},
            "data": {"required_fields": ["adj_close"], "warmup_lookback_days": 252},
        },
        "sample_backtest_spec": {
            "period_start": "2010-01-01",
            "period_end": "2024-12-31",
            "timeframe": "1D",
            "universe_used": "US_CORE_20",
            "initial_cash": 100000,
            "fee_bps": 1,
            "slippage_bps": 2,
        },
        "sample_performance": {
            "metrics": {"cagr_pct": 12.5, "volatility_pct": 16.1, "sortino": 1.2},
            "equity_curve": [{"date": "2024-12-31", "equity": 115600}],
        },
        "known_failure_modes": ["Sideways markets", "Regime shifts"],
        "risk_disclaimer": "Backtests are illustrative and not investment advice.",
        "entrypoint": "strategies.momentum_topn_v1:MomentumTopNStrategy",
        "code_version": "seed",
    },
    {
        "public_strategy_id": "trend_sma200_v1",
        "name": "Trend SMA200",
        "one_liner": "Risk-on above 200D SMA, else cash",
        "one_liner_ko": "벤치마크가 200일 이동평균 위이면 위험자산, 아래면 현금",
        "category": "trend",
        "tags": ["trend", "sma"],
        "risk_level": "low",
        "version": "1.0.0",
        "author_name": "QuantFairy",
        "author_type": "official",
        "sample_metrics": {
            "pnl_amount": 8200.0,
            "pnl_pct": 8.2,
            "sharpe": 0.9,
            "max_drawdown_pct": -8.8,
            "win_rate_pct": 52.1,
        },
        "sample_trade_stats": {"trades_count": 40, "avg_hold_hours": 240},
        "adds_count": 64,
        "likes_count": 22,
        "runs_count": 140,
        "supported_assets": ["US_Equity"],
        "supported_timeframes": ["1D"],
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
        "rules": {
            "signal_definition": "Price above SMA200.",
            "entry_rules": "Risk-on.",
            "exit_rules": "Risk-off to cash.",
            "rebalance_rule": "Daily.",
            "position_sizing": "All-in.",
        },
        "param_schema": {
            "type": "object",
            "properties": {
                "benchmark_symbol": {"type": "string", "default": "SPY"},
                "sma_window": {"type": "integer", "minimum": 100, "maximum": 300, "default": 200},
            },
            "required": ["benchmark_symbol", "sma_window"],
        },
        "default_params": {"benchmark_symbol": "SPY", "sma_window": 200},
        "recommended_presets": [],
        "requirements": {
            "universe": {"min_symbols": 1, "max_symbols": 1, "supports_custom_tickers": False},
            "data": {"required_fields": ["adj_close"], "warmup_lookback_days": 200},
        },
        "sample_backtest_spec": {
            "period_start": "2008-01-01",
            "period_end": "2024-12-31",
            "timeframe": "1D",
            "universe_used": "SPY",
            "initial_cash": 100000,
            "fee_bps": 1,
            "slippage_bps": 2,
        },
        "sample_performance": {
            "metrics": {"cagr_pct": 9.1, "volatility_pct": 10.0, "sortino": 1.0},
            "equity_curve": [{"date": "2024-12-31", "equity": 108200}],
        },
        "known_failure_modes": ["Whipsaws in choppy regimes"],
        "risk_disclaimer": "Backtests are illustrative and not investment advice.",
        "entrypoint": "strategies.trend_sma200_v1:TrendSMA200Strategy",
        "code_version": "seed",
    },
    {
        "public_strategy_id": "rsi_mean_reversion_v1",
        "name": "RSI Mean Reversion",
        "one_liner": "Buy RSI < 30, exit RSI > 50",
        "one_liner_ko": "RSI가 30 아래면 매수, 50 위면 청산",
        "category": "mean_reversion",
        "tags": ["rsi", "mean_reversion"],
        "risk_level": "mid",
        "version": "1.0.0",
        "author_name": "QuantFairy",
        "author_type": "official",
        "sample_metrics": {
            "pnl_amount": 6400.0,
            "pnl_pct": 6.4,
            "sharpe": 0.7,
            "max_drawdown_pct": -10.2,
            "win_rate_pct": 49.5,
        },
        "sample_trade_stats": {"trades_count": 60, "avg_hold_hours": 72},
        "adds_count": 48,
        "likes_count": 18,
        "runs_count": 95,
        "supported_assets": ["US_Equity"],
        "supported_timeframes": ["1D"],
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
        "rules": {
            "signal_definition": "RSI threshold.",
            "entry_rules": "RSI < 30 buy.",
            "exit_rules": "RSI > 50 sell.",
            "rebalance_rule": "Daily.",
            "position_sizing": "Single asset.",
        },
        "param_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "default": "SPY"},
                "rsi_window": {"type": "integer", "minimum": 7, "maximum": 30, "default": 14},
                "entry_rsi": {"type": "number", "minimum": 10, "maximum": 40, "default": 30},
                "exit_rsi": {"type": "number", "minimum": 40, "maximum": 70, "default": 50},
            },
            "required": ["symbol", "rsi_window", "entry_rsi", "exit_rsi"],
        },
        "default_params": {"symbol": "SPY", "rsi_window": 14, "entry_rsi": 30, "exit_rsi": 50},
        "recommended_presets": [],
        "requirements": {
            "universe": {"min_symbols": 1, "max_symbols": 1, "supports_custom_tickers": True},
            "data": {"required_fields": ["adj_close"], "warmup_lookback_days": 30},
        },
        "sample_backtest_spec": {
            "period_start": "2015-01-01",
            "period_end": "2024-12-31",
            "timeframe": "1D",
            "universe_used": "SPY",
            "initial_cash": 100000,
            "fee_bps": 1,
            "slippage_bps": 2,
        },
        "sample_performance": {
            "metrics": {"cagr_pct": 6.3, "volatility_pct": 12.4, "sortino": 0.8},
            "equity_curve": [{"date": "2024-12-31", "equity": 106400}],
        },
        "known_failure_modes": ["Strong trend markets"],
        "risk_disclaimer": "Backtests are illustrative and not investment advice.",
        "entrypoint": "strategies.rsi_mean_reversion_v1:RSIMeanReversionStrategy",
        "code_version": "seed",
    },
    {
        "public_strategy_id": "low_volatility_v1",
        "name": "Low Volatility",
        "one_liner": "Select low-volatility assets, monthly rebalance",
        "one_liner_ko": "변동성이 낮은 종목을 선별해 월간 리밸런싱",
        "category": "defensive",
        "tags": ["low_volatility", "defensive", "risk_control"],
        "risk_level": "low",
        "version": "1.0.0",
        "author_name": "QuantFairy",
        "author_type": "official",
        "sample_metrics": {
            "pnl_amount": 7200.0,
            "pnl_pct": 7.2,
            "sharpe": 1.1,
            "max_drawdown_pct": -6.1,
            "win_rate_pct": 56.4,
        },
        "sample_trade_stats": {"trades_count": 36, "avg_hold_hours": 240},
        "adds_count": 22,
        "likes_count": 9,
        "runs_count": 60,
        "supported_assets": ["US_Equity"],
        "supported_timeframes": ["1D"],
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
        "rules": {
            "signal_definition": "Rank by trailing volatility.",
            "entry_rules": "Buy lowest volatility assets.",
            "exit_rules": "Sell on rebalance.",
            "rebalance_rule": "Monthly.",
            "position_sizing": "Inverse-vol or equal weight.",
        },
        "param_schema": {
            "type": "object",
            "properties": {
                "lookback_days": {"type": "integer", "minimum": 20, "maximum": 252, "default": 60},
                "top_k": {"type": "integer", "minimum": 3, "maximum": 50, "default": 10},
                "weighting": {"type": "string", "enum": ["inverse_vol", "equal"], "default": "inverse_vol"},
                "rebalance": {"type": "string", "enum": ["monthly"], "default": "monthly"},
            },
            "required": ["lookback_days", "top_k"],
        },
        "default_params": {
            "lookback_days": 60,
            "top_k": 10,
            "weighting": "inverse_vol",
            "rebalance": "monthly",
        },
        "recommended_presets": [],
        "requirements": {
            "universe": {"min_symbols": 10, "max_symbols": 500, "supports_custom_tickers": True},
            "data": {"required_fields": ["adj_close"], "warmup_lookback_days": 60},
        },
        "sample_backtest_spec": {
            "period_start": "2012-01-01",
            "period_end": "2024-12-31",
            "timeframe": "1D",
            "universe_used": "US_CORE_20",
            "initial_cash": 100000,
            "fee_bps": 1,
            "slippage_bps": 2,
        },
        "sample_performance": {
            "metrics": {"cagr_pct": 8.4, "volatility_pct": 9.2, "sortino": 1.1},
            "equity_curve": [{"date": "2024-12-31", "equity": 107200}],
        },
        "known_failure_modes": ["Strong bull markets", "Volatility regime shifts"],
        "risk_disclaimer": "Backtests are illustrative and not investment advice.",
        "entrypoint": "strategies.low_volatility:LowVolatilityStrategy",
        "code_version": "seed",
    },
    {
        "public_strategy_id": "vol_adj_momentum_v1",
        "name": "Volatility-Adjusted Momentum",
        "one_liner": "Rank by return/volatility, monthly rebalance",
        "one_liner_ko": "수익/변동성 점수로 랭킹, 월간 리밸런싱",
        "category": "momentum",
        "tags": ["momentum", "volatility_adjusted"],
        "risk_level": "mid",
        "version": "1.0.0",
        "author_name": "QuantFairy",
        "author_type": "official",
        "sample_metrics": {
            "pnl_amount": 13800.0,
            "pnl_pct": 13.8,
            "sharpe": 1.3,
            "max_drawdown_pct": -9.5,
            "win_rate_pct": 57.9,
        },
        "sample_trade_stats": {"trades_count": 84, "avg_hold_hours": 120},
        "adds_count": 30,
        "likes_count": 12,
        "runs_count": 80,
        "supported_assets": ["US_Equity"],
        "supported_timeframes": ["1D"],
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
        "rules": {
            "signal_definition": "Return divided by volatility.",
            "entry_rules": "Buy top-K scores.",
            "exit_rules": "Sell on rebalance.",
            "rebalance_rule": "Monthly.",
            "position_sizing": "Equal weight.",
        },
        "param_schema": {
            "type": "object",
            "properties": {
                "lookback_days": {"type": "integer", "minimum": 60, "maximum": 504, "default": 252},
                "vol_window": {"type": "integer", "minimum": 20, "maximum": 252, "default": 60},
                "top_k": {"type": "integer", "minimum": 3, "maximum": 50, "default": 10},
                "rebalance": {"type": "string", "enum": ["monthly"], "default": "monthly"},
            },
            "required": ["lookback_days", "vol_window", "top_k"],
        },
        "default_params": {
            "lookback_days": 252,
            "vol_window": 60,
            "top_k": 10,
            "rebalance": "monthly",
        },
        "recommended_presets": [],
        "requirements": {
            "universe": {"min_symbols": 20, "max_symbols": 500, "supports_custom_tickers": True},
            "data": {"required_fields": ["adj_close"], "warmup_lookback_days": 252},
        },
        "sample_backtest_spec": {
            "period_start": "2010-01-01",
            "period_end": "2024-12-31",
            "timeframe": "1D",
            "universe_used": "US_CORE_20",
            "initial_cash": 100000,
            "fee_bps": 1,
            "slippage_bps": 2,
        },
        "sample_performance": {
            "metrics": {"cagr_pct": 11.3, "volatility_pct": 14.5, "sortino": 1.15},
            "equity_curve": [{"date": "2024-12-31", "equity": 113800}],
        },
        "known_failure_modes": ["Momentum crashes", "High-volatility reversals"],
        "risk_disclaimer": "Backtests are illustrative and not investment advice.",
        "entrypoint": "strategies.vol_adj_momentum:VolatilityAdjustedMomentumStrategy",
        "code_version": "seed",
    },
    {
        "public_strategy_id": "risk_on_off_v1",
        "name": "Risk-On / Risk-Off Rotation",
        "one_liner": "Rotate to cash when benchmark falls below SMA",
        "one_liner_ko": "벤치마크가 SMA 아래면 현금, 위면 위험자산 바스켓",
        "category": "regime",
        "tags": ["regime", "trend", "risk_on_off"],
        "risk_level": "low",
        "version": "1.0.0",
        "author_name": "QuantFairy",
        "author_type": "official",
        "sample_metrics": {
            "pnl_amount": 9100.0,
            "pnl_pct": 9.1,
            "sharpe": 1.0,
            "max_drawdown_pct": -7.4,
            "win_rate_pct": 53.2,
        },
        "sample_trade_stats": {"trades_count": 40, "avg_hold_hours": 240},
        "adds_count": 26,
        "likes_count": 10,
        "runs_count": 70,
        "supported_assets": ["US_Equity"],
        "supported_timeframes": ["1D"],
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
        "rules": {
            "signal_definition": "Benchmark vs SMA.",
            "entry_rules": "Risk-on when above SMA.",
            "exit_rules": "Move to cash when below SMA.",
            "rebalance_rule": "Monthly.",
            "position_sizing": "Equal weight basket.",
        },
        "param_schema": {
            "type": "object",
            "properties": {
                "benchmark_symbol": {"type": "string", "default": "SPY"},
                "sma_window": {"type": "integer", "minimum": 100, "maximum": 300, "default": 200},
                "lookback_days": {"type": "integer", "minimum": 60, "maximum": 252, "default": 126},
                "top_k": {"type": "integer", "minimum": 3, "maximum": 50, "default": 10},
                "rebalance": {"type": "string", "enum": ["monthly"], "default": "monthly"},
            },
            "required": ["benchmark_symbol", "sma_window", "lookback_days", "top_k"],
        },
        "default_params": {
            "benchmark_symbol": "SPY",
            "sma_window": 200,
            "lookback_days": 126,
            "top_k": 10,
            "rebalance": "monthly",
        },
        "recommended_presets": [],
        "requirements": {
            "universe": {"min_symbols": 10, "max_symbols": 500, "supports_custom_tickers": True},
            "data": {"required_fields": ["adj_close"], "warmup_lookback_days": 200},
        },
        "sample_backtest_spec": {
            "period_start": "2008-01-01",
            "period_end": "2024-12-31",
            "timeframe": "1D",
            "universe_used": "US_CORE_20",
            "initial_cash": 100000,
            "fee_bps": 1,
            "slippage_bps": 2,
        },
        "sample_performance": {
            "metrics": {"cagr_pct": 9.4, "volatility_pct": 10.2, "sortino": 1.05},
            "equity_curve": [{"date": "2024-12-31", "equity": 109100}],
        },
        "known_failure_modes": ["Whipsaws in sideways markets"],
        "risk_disclaimer": "Backtests are illustrative and not investment advice.",
        "entrypoint": "strategies.risk_on_off:RiskOnOffStrategy",
        "code_version": "seed",
    },
]

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

def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


class PublicStrategiesRepository:
    def __init__(self, settings: Settings) -> None:
        self.supabase = get_supabase_client(settings)

    def ensure_seed(self) -> None:
        if self.supabase is None:
            return
        try:
            result = (
                self.supabase.table("public_strategies")
                .select(
                    "public_strategy_id, one_liner, one_liner_ko, "
                    "full_description, full_description_ko, thesis, thesis_ko"
                )
                .execute()
            )
            existing_rows = {
                row["public_strategy_id"]: row for row in (getattr(result, "data", None) or [])
            }
            now = now_kst().isoformat()
            rows: List[Dict[str, Any]] = []
            updates: List[Tuple[str, Dict[str, Any]]] = []
            for item in DEFAULT_PUBLIC_STRATEGIES:
                strategy_id = item["public_strategy_id"]
                existing = existing_rows.get(strategy_id)
                if not existing:
                    rows.append(
                        {
                            **item,
                            "created_at": now,
                            "updated_at": now,
                        }
                    )
                    continue

                update_payload: Dict[str, Any] = {}
                for field in ("one_liner_ko", "full_description_ko", "thesis_ko"):
                    if item.get(field) and _is_blank(existing.get(field)):
                        update_payload[field] = item[field]

                legacy_full = LEGACY_FULL_DESCRIPTION.get(strategy_id)
                if item.get("full_description") and (
                    _is_blank(existing.get("full_description"))
                    or (legacy_full and existing.get("full_description") == legacy_full)
                ):
                    update_payload["full_description"] = item["full_description"]

                legacy_thesis = LEGACY_THESIS.get(strategy_id)
                if item.get("thesis") and (
                    _is_blank(existing.get("thesis"))
                    or (legacy_thesis and existing.get("thesis") == legacy_thesis)
                ):
                    update_payload["thesis"] = item["thesis"]

                if update_payload:
                    update_payload["updated_at"] = now
                    updates.append((strategy_id, update_payload))
            if rows:
                self.supabase.table("public_strategies").insert(rows).execute()
            for strategy_id, payload in updates:
                try:
                    (
                        self.supabase.table("public_strategies")
                        .update(payload)
                        .eq("public_strategy_id", strategy_id)
                        .execute()
                    )
                except Exception:
                    continue
        except Exception:
            return

    def list(
        self,
        filters: Dict[str, Any],
        sort: str,
        order: str,
        limit: int,
        cursor_value: Optional[str],
    ) -> List[Dict[str, Any]]:
        if self.supabase is None:
            return DEFAULT_PUBLIC_STRATEGIES[:limit]
        query = self.supabase.table("public_strategies").select("*")

        if filters.get("q"):
            q = filters["q"]
            query = query.or_(f"name.ilike.%{q}%,one_liner.ilike.%{q}%")
        if filters.get("tag"):
            query = query.contains("tags", [filters["tag"]])
        if filters.get("category"):
            query = query.eq("category", filters["category"])
        if filters.get("risk_level"):
            query = query.eq("risk_level", filters["risk_level"])

        if cursor_value:
            op = "lt" if order == "desc" else "gt"
            query = query.filter(sort, op, cursor_value)

        query = query.order(sort, desc=(order == "desc")).limit(limit)
        result = query.execute()
        data = getattr(result, "data", None)
        return data or []

    def get(self, public_strategy_id: str) -> Optional[Dict[str, Any]]:
        if self.supabase is None:
            for item in DEFAULT_PUBLIC_STRATEGIES:
                if item["public_strategy_id"] == public_strategy_id:
                    return item
            return None
        try:
            result = (
                self.supabase.table("public_strategies")
                .select("*")
                .eq("public_strategy_id", public_strategy_id)
                .limit(1)
                .execute()
            )
            data = getattr(result, "data", None)
            if data:
                return data[0]
        except Exception:
            return None
        return None
