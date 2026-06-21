"""Shared pytest fixtures and helpers for the Cop–Thief test suite."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Environment helpers
# ---------------------------------------------------------------------------


@pytest.fixture()
def minimal_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set the minimum required env vars so config loading doesn't fail fast."""
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("MCP_COP_TOKEN", "test-cop-token")
    monkeypatch.setenv("MCP_THIEF_TOKEN", "test-thief-token")


# ---------------------------------------------------------------------------
# Config file helpers
# ---------------------------------------------------------------------------


@pytest.fixture()
def valid_config_yaml(tmp_path: Path) -> Path:
    """Write a minimal but valid config.yaml to *tmp_path* and return its path."""
    cfg = textwrap.dedent(
        """\
        grid_size: [5, 5]
        max_moves: 25
        num_games: 6
        max_barriers: 5
        scoring:
          cop_win: 20
          thief_win: 10
          cop_loss: 5
          thief_loss: 5
        start_mode: random
        thief_moves_first: true
        discount_gamma: 0.95
        strategy: heuristic
        llm:
          provider: openai
          model: gpt-4o-mini
          timeout_s: 30
        mcp:
          cop_url: "http://localhost:8001"
          thief_url: "http://localhost:8002"
        gatekeeper:
          rate_limit_per_target: 5
          max_retries: 3
          queue_size: 64
          timeout_s: 30
        email:
          to: "test@example.com"
        timezone: "UTC"
        seed: 42
        """
    )
    config_file = tmp_path / "config.yaml"
    config_file.write_text(cfg, encoding="utf-8")
    return config_file
