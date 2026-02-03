from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.config import Settings
from app.core.time import now_kst
from app.storage.supabase_client import get_supabase_client


DEFAULT_PUBLIC_STRATEGIES = [
    {
        "public_strategy_id": "momentum_top10_12m_v1",
        "name": "Momentum Top-10 (12M)",
        "one_liner": "Top-N by 12M return, monthly rebalance",
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
        "full_description": "Cross-sectional momentum using 12M returns.",
        "thesis": "Buy top performers and rebalance monthly.",
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
        "full_description": "Simple trend following on SMA200.",
        "thesis": "Risk-on when above SMA200, else cash.",
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
        "full_description": "RSI mean reversion strategy.",
        "thesis": "Buy oversold, exit on mean reversion.",
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
        "full_description": "Low volatility selection with inverse-vol or equal weighting.",
        "thesis": "Lower vol assets tend to defend in drawdowns.",
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
        "full_description": "Momentum ranked by return/volatility to reduce crash risk.",
        "thesis": "Risk-adjusted momentum improves robustness.",
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
        "full_description": "Risk-on basket when benchmark above SMA, otherwise cash.",
        "thesis": "Regime filter reduces large drawdowns.",
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


class PublicStrategiesRepository:
    def __init__(self, settings: Settings) -> None:
        self.supabase = get_supabase_client(settings)

    def ensure_seed(self) -> None:
        if self.supabase is None:
            return
        try:
            result = (
                self.supabase.table("public_strategies")
                .select("public_strategy_id")
                .execute()
            )
            existing = {row["public_strategy_id"] for row in (getattr(result, "data", None) or [])}
            now = now_kst().isoformat()
            rows = []
            for item in DEFAULT_PUBLIC_STRATEGIES:
                if item["public_strategy_id"] in existing:
                    continue
                rows.append(
                    {
                        **item,
                        "created_at": now,
                        "updated_at": now,
                    }
                )
            if rows:
                self.supabase.table("public_strategies").insert(rows).execute()
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
