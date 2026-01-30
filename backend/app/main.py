from fastapi import FastAPI

app = FastAPI(title="Madcamp Week4 API")

@app.get("/")
def read_root():
    return {"message": "FastAPI is running"}

# 샘플 전체 데이터
EQUITY_CURVE = [
    {"t": "2026-01-01T00:00:00+09:00", "equity": 95000.0},
    {"t": "2026-01-03T00:00:00+09:00", "equity": 95500.0},
    {"t": "2026-01-05T00:00:00+09:00", "equity": 96000.0},
    {"t": "2026-01-07T00:00:00+09:00", "equity": 97000.0},
    {"t": "2026-01-09T00:00:00+09:00", "equity": 96500.0},
    {"t": "2026-01-11T00:00:00+09:00", "equity": 98000.0},
    {"t": "2026-01-13T00:00:00+09:00", "equity": 99000.0},
    {"t": "2026-01-15T00:00:00+09:00", "equity": 100500.0},
    {"t": "2026-01-17T00:00:00+09:00", "equity": 101200.0},
    {"t": "2026-01-19T00:00:00+09:00", "equity": 102000.0},
    {"t": "2026-01-21T00:00:00+09:00", "equity": 101500.0},
    {"t": "2026-01-23T00:00:00+09:00", "equity": 103000.0},
    {"t": "2026-01-25T00:00:00+09:00", "equity": 104200.0},
    {"t": "2026-01-27T00:00:00+09:00", "equity": 105800.0},
    {"t": "2026-01-29T00:00:00+09:00", "equity": 106900.0},
]

def slice_curve(range: str):
    if range == "1D":
        return EQUITY_CURVE[-2:]
    if range == "1W":
        return EQUITY_CURVE[-5:]
    if range == "1M":
        return EQUITY_CURVE[-15:]
    if range == "3M":
        return EQUITY_CURVE[-15:]
    if range == "1Y":
        return EQUITY_CURVE[-15:]
    return EQUITY_CURVE  # ALL

@app.get("/api/v1/dashboard")
def get_dashboard(range: str = "1M"):
    curve = slice_curve(range)

    return {
        "mode": {"environment": "paper", "kill_switch": False},
        "status": {
            "broker": {"state": "connected", "latency_ms": 120},
            "worker": {"state": "running", "last_heartbeat_at": "2026-01-29T16:39:58+09:00"},
            "data": {"state": "ok", "lag_seconds": 2},
        },
        "account": {
            "equity": 100000.0,
            "cash": 25000.0,
            "buying_power": 75000.0,
            "currency": "USD",
            "updated_at": "2026-01-29T16:40:00+09:00",
        },
        "kpi": {
            "today_pnl": {"value": 123.45, "pct": 0.12},
            "total_pnl": {"value": 15600.0, "pct": 15.6},
            "active_positions": {"count": 5, "new_today": 2},
            "selected_metric": {"name": "max_drawdown", "value": -4.2, "unit": "pct", "window": range},
        },
        "performance": {
            "range": range,
            "equity_curve": curve,
            "summary": {"return_pct": 12.53, "max_drawdown_pct": -2.10},
        },
        "bot": {
            "state": "running",
            "last_run": {
                "run_id": "run_20260129_001",
                "started_at": "2026-01-29T09:35:00+09:00",
                "ended_at": "2026-01-29T09:35:12+09:00",
                "result": "success",
                "orders_created": 4,
                "orders_failed": 0,
            },
            "next_run_at": "2026-01-30T09:35:00+09:00",
        },
        "active_strategies": [
            {
                "strategy_id": "strat_momentum_top10",
                "name": "Momentum Breakout",
                "state": "running",
                "positions_count": 2,
                "pnl_today": {"value": 1240.2, "pct": 1.24},
            }
        ],
        "recent_trades": [
            {
                "fill_id": "fill_001",
                "filled_at": "2026-01-29T14:32:15+09:00",
                "symbol": "AAPL",
                "side": "buy",
                "qty": 100,
                "price": 178.25,
                "strategy_id": "strat_mean_reversion",
                "strategy_name": "Mean Reversion Alpha",
            }
        ],
        "alerts": [],
    }


# 모드 전환
@app.post("/api/v1/trading/mode")
def set_mode(payload: dict):
    return {"environment": payload.get("environment", "paper")}

# 킬 스위치
@app.post("/api/v1/trading/kill-switch")
def set_kill_switch(payload: dict):
    return {"enabled": payload.get("enabled", False)}

# 봇 제어
@app.post("/api/v1/bot/start")
def bot_start():
    return {"state": "running"}

@app.post("/api/v1/bot/stop")
def bot_stop():
    return {"state": "stopped"}

@app.post("/api/v1/bot/run-now")
def bot_run_now():
    return {"run_id": "run_20260129_manual_001", "state": "queued"}