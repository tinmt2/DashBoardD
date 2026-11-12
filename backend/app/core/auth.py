import os
import json
import time
from typing import Optional
from fastapi import Header, HTTPException

CONFIG_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "admin_config.json"))
ADMIN_TOKEN_TTL_SECONDS = 8 * 3600  # 8 hours default session TTL


def get_admin_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "admin_username": "admin",
        "active_tokens": []
    }


def save_admin_config(cfg: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def verify_admin_token(authorization: Optional[str] = Header(None)) -> str:
    """
    Validates Bearer token against active_tokens with TTL check.
    Prunes expired tokens and rejects unauthorized requests with HTTP 401.
    """
    if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Chưa có token xác thực!")

    token = authorization[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Token không hợp lệ!")

    cfg = get_admin_config()
    now = time.time()
    active_tokens = cfg.get("active_tokens", [])

    valid_token_found = False
    cleaned_tokens = []

    for t in active_tokens:
        created_at = t.get("created_at", 0)
        # Check token validity and TTL
        if now - created_at < ADMIN_TOKEN_TTL_SECONDS:
            cleaned_tokens.append(t)
            if t.get("token") == token:
                valid_token_found = True

    # Prune expired tokens if list changed
    if len(cleaned_tokens) != len(active_tokens):
        cfg["active_tokens"] = cleaned_tokens
        save_admin_config(cfg)

    if not valid_token_found:
        raise HTTPException(status_code=401, detail="Phiên đăng nhập Admin đã hết hạn hoặc không hợp lệ!")

    return token


def revoke_admin_token(token: str):
    """
    Revokes an active token upon logout.
    """
    cfg = get_admin_config()
    tokens = [t for t in cfg.get("active_tokens", []) if t.get("token") != token]
    cfg["active_tokens"] = tokens
    save_admin_config(cfg)
