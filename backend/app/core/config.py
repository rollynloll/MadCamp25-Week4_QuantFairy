import os
from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv


# 로컬에서만 .env 로드 (Render는 대시보드 env 사용)
if os.getenv("ENV", "").lower() not in {"prod", "production"}:
    load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str
    alpaca_api_key: str | None
    alpaca_secret_key: str | None
    alpaca_base_url: str
    alpaca_data_stream_url: str | None
    alpaca_data_feed: str
    alpaca_oauth_client_id: str | None
    alpaca_oauth_client_secret: str | None
    alpaca_oauth_redirect_url: str | None
    alpaca_oauth_scope: str | None
    supabase_url: str | None
    supabase_service_role_key: str | None
    oauth_state_secret: str | None
    frontend_base_url: str | None
    default_user_id: str | None
    api_token: str | None
    allow_live_trading: bool
    cors_origins: List[str]


def _get_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_list(name: str, default: List[str]) -> List[str]:
    value = os.getenv(name)
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


def _get_env(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return None


def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "QuantFairy API"),
        alpaca_api_key=_get_env("ALPACA_API_KEY", "ALPACA_API_KEY_ID"),
        alpaca_secret_key=_get_env("ALPACA_SECRET_KEY", "ALPACA_API_SECRET_KEY"),
        alpaca_base_url=os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"),
        alpaca_data_stream_url=os.getenv("ALPACA_DATA_STREAM_URL"),
        alpaca_data_feed=os.getenv("ALPACA_DATA_FEED", "iex"),
        alpaca_oauth_client_id=os.getenv("ALPACA_OAUTH_CLIENT_ID"),
        alpaca_oauth_client_secret=os.getenv("ALPACA_OAUTH_CLIENT_SECRET"),
        alpaca_oauth_redirect_url=os.getenv("ALPACA_OAUTH_REDIRECT_URL"),
        alpaca_oauth_scope=os.getenv("ALPACA_OAUTH_SCOPE"),
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
        oauth_state_secret=os.getenv("OAUTH_STATE_SECRET"),
        frontend_base_url=os.getenv("FRONTEND_BASE_URL"),
        default_user_id=os.getenv("DEFAULT_USER_ID"),
        api_token=os.getenv("API_TOKEN"),
        allow_live_trading=_get_bool("ALLOW_LIVE_TRADING", False),
        cors_origins=_get_list(
            "CORS_ORIGINS",
            [
                "https://quant.seungwoon.com",
                "https://api.quant.seungwoon.com",
                "http://localhost:5173",
                "http://localhost:3000",
            ],
        ),
    )
