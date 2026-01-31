from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.config import Settings
from app.core.time import now_kst
from app.storage.supabase_client import get_supabase_client


DEFAULT_PUBLIC_STRATEGIES = [
    {
        "public_strategy_id": "pub_momentum_top10",
        "name": "Momentum Breakout",
        "one_liner": "Top-10 momentum breakout strategy",
        "category": "momentum",
        "tags": ["momentum", "trend"],
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
        "full_description": "Momentum breakout strategy.",
        "thesis": "Trend following with weekly rebalance.",
        "rules": {
            "signal_definition": "Rank by 3M return.",
            "entry_rules": "Buy top-k.",
            "exit_rules": "Sell on rebalance.",
            "rebalance_rule": "Weekly.",
            "position_sizing": "Equal weight.",
            "risk_management": "Max position 20%.",
        },
        "param_schema": {
            "type": "object",
            "properties": {
                "lookback": {"type": "integer", "minimum": 2, "maximum": 252, "default": 60},
                "top_k": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
                "rebalance": {
                    "type": "string",
                    "enum": ["daily", "weekly", "monthly"],
                    "default": "weekly",
                },
            },
            "required": ["lookback", "top_k", "rebalance"],
        },
        "default_params": {"lookback": 60, "top_k": 10, "rebalance": "weekly"},
        "recommended_presets": [
            {"preset_name": "Default", "params": {"lookback": 60, "top_k": 10, "rebalance": "weekly"}, "description": "Default preset"}
        ],
        "requirements": {
            "universe": {"min_symbols": 10, "max_symbols": 200, "supports_custom_tickers": True},
            "data": {"required_fields": ["close"], "warmup_lookback_days": 60},
        },
        "sample_backtest_spec": {
            "period_start": "2020-01-01",
            "period_end": "2024-12-31",
            "timeframe": "1D",
            "universe_used": "US_TOP_500",
            "initial_cash": 100000,
            "fee_bps": 1,
            "slippage_bps": 2,
        },
        "sample_performance": {
            "metrics": {"cagr_pct": 12.5, "volatility_pct": 16.1, "sortino": 1.2},
            "equity_curve": [{"date": "2024-12-31", "equity": 115600}],
        },
        "known_failure_modes": ["Choppy market"],
        "risk_disclaimer": "Not investment advice.",
    }
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
                .limit(1)
                .execute()
            )
            if getattr(result, "data", None):
                return
            now = now_kst().isoformat()
            rows = []
            for item in DEFAULT_PUBLIC_STRATEGIES:
                rows.append(
                    {
                        **item,
                        "created_at": now,
                        "updated_at": now,
                    }
                )
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
