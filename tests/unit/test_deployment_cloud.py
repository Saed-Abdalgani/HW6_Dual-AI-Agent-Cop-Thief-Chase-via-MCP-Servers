"""Unit tests for cloud deployment helpers."""

from __future__ import annotations

import pytest

from cop_thief.services.deployment.cloud import (
    assert_hybrid_client_safe,
    cloud_urls_ready,
    is_deployed_url,
    resolve_mcp_wiring,
)
from cop_thief.shared.config import Config


def test_is_deployed_url_rejects_placeholders() -> None:
    assert is_deployed_url("https://replace-with-cop-mcp.example.com") is False
    assert is_deployed_url("https://cop-mcp.onrender.com") is True


def test_resolve_mcp_wiring_localhost_uses_direct(valid_config_yaml: object) -> None:
    cfg = Config.from_yaml(str(valid_config_yaml))
    assert resolve_mcp_wiring(cfg) == (True, False)


def test_resolve_mcp_wiring_http_localhost_auto_launches() -> None:
    cfg = Config.model_validate(
        {
            "email": {"to": "test@example.com"},
            "mcp": {
                "mode": "http",
                "auto_launch": True,
                "cop_url": "http://localhost:8001",
                "thief_url": "http://127.0.0.1:8002",
            },
        },
    )
    assert resolve_mcp_wiring(cfg) == (False, True)


def test_resolve_mcp_wiring_http_localhost_can_skip_auto_launch() -> None:
    cfg = Config.model_validate(
        {
            "email": {"to": "test@example.com"},
            "mcp": {
                "mode": "http",
                "auto_launch": False,
                "cop_url": "http://localhost:8001",
                "thief_url": "http://localhost:8002",
            },
        },
    )
    assert resolve_mcp_wiring(cfg) == (False, False)


def test_resolve_mcp_wiring_cloud_uses_remote() -> None:
    cfg = Config.model_validate(
        {
            "email": {"to": "test@example.com"},
            "mcp": {
                "mode": "auto",
                "cop_url": "https://cop-thief-cop.onrender.com",
                "thief_url": "https://cop-thief-thief.onrender.com",
            },
        },
    )
    assert resolve_mcp_wiring(cfg) == (False, False)
    assert cloud_urls_ready(cfg) is True


def test_assert_hybrid_client_safe_rejects_local_ollama() -> None:
    cfg = Config.model_validate(
        {
            "email": {"to": "test@example.com"},
            "mcp": {
                "cop_url": "https://cop-thief-cop.onrender.com",
                "thief_url": "https://cop-thief-thief.onrender.com",
            },
            "llm": {
                "provider": "ollama",
                "model": "llama3",
                "base_url": "http://localhost:11434",
            },
        },
    )
    with pytest.raises(ValueError, match="Hybrid cloud mode"):
        assert_hybrid_client_safe(cfg)
