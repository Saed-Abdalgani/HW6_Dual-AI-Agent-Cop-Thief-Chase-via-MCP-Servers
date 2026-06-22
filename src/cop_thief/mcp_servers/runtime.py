"""Runtime helpers for local and cloud MCP server startup.

Traces: FR-MCP5, NFR-1, NFR-2, NFR-3, T-P7-01, T-P7-06.
"""

from __future__ import annotations

import os
from urllib.parse import urlparse

from cop_thief.shared.auth import default_store
from cop_thief.shared.config import Config


def seed_tokens_from_env() -> None:
    """Register configured bearer tokens and deploy-time revocations."""
    for agent, env_var in [("cop", "MCP_COP_TOKEN"), ("thief", "MCP_THIEF_TOKEN")]:
        value = os.environ.get(env_var)
        if value:
            default_store.register_token(agent, value)
    for token in _csv_env("MCP_REVOKED_TOKENS"):
        default_store.register_token("revoked", token)
        default_store.revoke(token)


def role_from_env() -> str:
    """Return ``SERVER_ROLE`` as ``cop`` or ``thief``."""
    role = os.environ.get("SERVER_ROLE", "cop").strip().lower()
    if role not in {"cop", "thief"}:
        msg = "SERVER_ROLE must be 'cop' or 'thief'."
        raise ValueError(msg)
    return role


def bind_host_port(config: Config, role: str) -> tuple[str, int]:
    """Return host/port for local or cloud runtime.

    Cloud providers commonly inject ``PORT``; when present it wins over the
    configured URL port while keeping URLs config-driven for clients.
    """
    url = urlparse(config.mcp.cop_url if role == "cop" else config.mcp.thief_url)
    host = os.environ.get("MCP_HOST") or url.hostname or "0.0.0.0"
    port = int(os.environ.get("PORT") or url.port or (8001 if role == "cop" else 8002))
    return host, port


def _csv_env(name: str) -> list[str]:
    return [item.strip() for item in os.environ.get(name, "").split(",") if item.strip()]
