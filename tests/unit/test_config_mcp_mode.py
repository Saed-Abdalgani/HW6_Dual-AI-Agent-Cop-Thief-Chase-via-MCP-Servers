"""Config coverage for MCP wiring mode overrides."""

from __future__ import annotations

from pathlib import Path

import pytest

from cop_thief.shared.config import Config


def test_from_env_overrides_mcp_mode(
    valid_config_yaml: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CONFIG_PATH", str(valid_config_yaml))
    monkeypatch.setenv("MCP_MODE", "http")
    monkeypatch.setenv("MCP_AUTO_LAUNCH", "false")

    cfg = Config.from_env()

    assert cfg.mcp.mode == "http"
    assert cfg.mcp.auto_launch is False
