"""Tests for Phase P7 cloud runtime helpers."""

from __future__ import annotations

import pytest

from cop_thief.mcp_servers import runtime
from cop_thief.shared.auth import default_store
from cop_thief.shared.config import Config


def test_role_from_env_accepts_cop(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERVER_ROLE", "cop")
    assert runtime.role_from_env() == "cop"


def test_role_from_env_rejects_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERVER_ROLE", "owl")
    with pytest.raises(ValueError, match="SERVER_ROLE"):
        runtime.role_from_env()


def test_bind_host_port_prefers_cloud_port(
    valid_config_yaml: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = Config.from_yaml(str(valid_config_yaml))
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("MCP_HOST", "0.0.0.0")
    assert runtime.bind_host_port(cfg, "thief") == ("0.0.0.0", 9000)


def test_seed_tokens_from_env_registers_and_revokes(monkeypatch: pytest.MonkeyPatch) -> None:
    cop_token = "cloud-cop-token"
    thief_token = "cloud-thief-token"
    old_token = "old-cloud-token"
    monkeypatch.setenv("MCP_COP_TOKEN", cop_token)
    monkeypatch.setenv("MCP_THIEF_TOKEN", thief_token)
    monkeypatch.setenv("MCP_REVOKED_TOKENS", old_token)
    runtime.seed_tokens_from_env()
    assert default_store.get_agent(cop_token) == "cop"
    assert default_store.get_agent(thief_token) == "thief"
    assert default_store.get_agent(old_token) is None
