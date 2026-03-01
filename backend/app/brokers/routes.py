from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
from datetime import timedelta
from typing import Any, Dict
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from app.core.config import get_settings
from app.core.time import now_kst
from app.storage.broker_tokens_repo import BrokerTokensRepository
from app.storage.user_accounts_repo import UserAccountsRepository
from app.storage.users_repo import UsersRepository

logger = logging.getLogger("uvicorn.error")

router = APIRouter(tags=["brokers"])

ALPACA_OAUTH_AUTHORIZE_URL = "https://app.alpaca.markets/oauth/authorize"
ALPACA_OAUTH_TOKEN_URL = "https://api.alpaca.markets/oauth/token"
ALPACA_PAPER_API_BASE = "https://paper-api.alpaca.markets"
ALPACA_LIVE_API_BASE = "https://api.alpaca.markets"


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _build_state(payload: Dict[str, Any], secret: str | None) -> str:
    raw = json.dumps(payload, separators=(",", ":")).encode()
    encoded = _b64url_encode(raw)
    if not secret:
        return encoded
    sig = hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).hexdigest()
    return f"{encoded}.{sig}"


def _parse_state(state: str, secret: str | None) -> Dict[str, Any]:
    if "." in state:
        encoded, sig = state.rsplit(".", 1)
        if secret:
            expected = hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected, sig):
                raise ValueError("Invalid state signature")
    else:
        encoded = state
    payload = json.loads(_b64url_decode(encoded))
    if not isinstance(payload, dict):
        raise ValueError("Invalid state payload")
    return payload


@router.get("/brokers/alpaca/oauth/start")
def alpaca_oauth_start(
    user_id: str = Query(...),
    environment: str = Query(default="paper"),
    return_to: str | None = Query(default=None),
):
    settings = get_settings()
    if not settings.alpaca_oauth_client_id or not settings.alpaca_oauth_redirect_url:
        raise HTTPException(status_code=500, detail="Alpaca OAuth is not configured")

    env = "live" if environment == "live" else "paper"
    payload = {
        "user_id": user_id,
        "environment": env,
        "return_to": return_to,
    }
    state = _build_state(payload, settings.oauth_state_secret)

    params = {
        "response_type": "code",
        "client_id": settings.alpaca_oauth_client_id,
        "redirect_uri": settings.alpaca_oauth_redirect_url,
        "state": state,
        "env": env,
    }
    if settings.alpaca_oauth_scope:
        params["scope"] = settings.alpaca_oauth_scope
    auth_url = f"{ALPACA_OAUTH_AUTHORIZE_URL}?{urlencode(params)}"
    return RedirectResponse(auth_url, status_code=302)


@router.get("/brokers/alpaca/oauth/callback")
def alpaca_oauth_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
):
    settings = get_settings()
    if not settings.alpaca_oauth_client_id or not settings.alpaca_oauth_client_secret:
        raise HTTPException(status_code=500, detail="Alpaca OAuth is not configured")

    return_to = settings.frontend_base_url or ""
    try:
        if state:
            payload = _parse_state(state, settings.oauth_state_secret)
            return_to = payload.get("return_to") or return_to
            user_id = payload.get("user_id")
            environment = payload.get("environment", "paper")
        else:
            user_id = None
            environment = "paper"
    except Exception as exc:
        logger.warning("alpaca.oauth invalid state: %s", exc)
        return RedirectResponse(f"{return_to}/onboarding/connect?status=failed", status_code=302)

    if error or not code or not user_id:
        return RedirectResponse(f"{return_to}/onboarding/connect?status=failed", status_code=302)

    try:
        token_res = requests.post(
            ALPACA_OAUTH_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.alpaca_oauth_client_id,
                "client_secret": settings.alpaca_oauth_client_secret,
                "redirect_uri": settings.alpaca_oauth_redirect_url,
            },
            timeout=10,
        )
        token_res.raise_for_status()
        token_payload = token_res.json()
    except Exception as exc:
        logger.error("alpaca.oauth token exchange failed: %s", exc)
        return RedirectResponse(f"{return_to}/onboarding/connect?status=failed", status_code=302)

    access_token = token_payload.get("access_token")
    if not access_token:
        return RedirectResponse(f"{return_to}/onboarding/connect?status=failed", status_code=302)

    UsersRepository(settings).ensure(user_id)

    expires_in = token_payload.get("expires_in")
    expires_at = None
    if isinstance(expires_in, (int, float)):
        expires_at = (now_kst() + timedelta(seconds=int(expires_in))).isoformat()

    BrokerTokensRepository(settings).upsert_token(
        user_id=user_id,
        broker="alpaca",
        environment=environment,
        access_token=access_token,
        refresh_token=token_payload.get("refresh_token"),
        token_type=token_payload.get("token_type"),
        scope=token_payload.get("scope"),
        expires_at=expires_at,
    )

    base_url = ALPACA_PAPER_API_BASE if environment == "paper" else ALPACA_LIVE_API_BASE
    try:
        account_res = requests.get(
            f"{base_url}/v2/account",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        account_res.raise_for_status()
        account = account_res.json()
    except Exception as exc:
        logger.error("alpaca.oauth account fetch failed: %s", exc)
        return RedirectResponse(f"{return_to}/onboarding/connect?status=failed", status_code=302)

    UserAccountsRepository(settings).upsert_account(
        user_id=user_id,
        environment=environment,
        account_id=str(account.get("id") or "alpaca_account"),
        equity=float(account.get("equity", 0)),
        cash=float(account.get("cash", 0)),
        buying_power=float(account.get("buying_power", 0)),
        currency=str(account.get("currency") or "USD"),
    )

    return RedirectResponse(f"{return_to}/onboarding/connect?status=connected", status_code=302)
