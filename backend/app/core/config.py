import os
from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str
    alpaca_api_key: str | None
    alpaca_secret_key: str | None
    alpaca_base_url: str
    supabase_url: str | None
    supabase_service_role_key: str | None
    default_user_id: str | None
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


def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "QuantFairy API"),
        alpaca_api_key=os.getenv("ALPACA_API_KEY"),
        alpaca_secret_key=os.getenv("ALPACA_SECRET_KEY"),
        alpaca_base_url=os.getenv(
            "ALPACA_BASE_URL", "https://paper-api.alpaca.markets"
        ),
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
        default_user_id=os.getenv("DEFAULT_USER_ID"),
        allow_live_trading=_get_bool("ALLOW_LIVE_TRADING", False),
        cors_origins=_get_list(
            "CORS_ORIGINS",
            [
                "https://quant.seungwoon.com",
                "http://localhost:5173",
                "http://localhost:3000",
            ],
        ),
    )
