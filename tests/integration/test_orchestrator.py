"""Integration tests for orchestrator full-game loop with mocked externals."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from cop_thief.constants import Outcome
from cop_thief.mcp_servers import _state
from cop_thief.sdk.facade import CopThiefSDK
from cop_thief.shared.auth import default_store


@pytest.fixture()
def fast_config(tmp_path: Path, minimal_env: None, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Config with max_moves=2 for fast sub-games."""
    cfg = textwrap.dedent(
        """\
        grid_size: [5, 5]
        max_moves: 2
        num_games: 6
        max_barriers: 1
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
          rate_limit_per_target: 100
          max_retries: 1
          queue_size: 64
          timeout_s: 30
        email:
          to: "test@example.com"
        timezone: "UTC"
        seed: 42
        """
    )
    path = tmp_path / "config.yaml"
    path.write_text(cfg, encoding="utf-8")
    monkeypatch.setenv("CONFIG_PATH", str(path))
    state_file = tmp_path / "mcp_state.json"
    monkeypatch.setattr(_state, "STATE_PATH", state_file)
    default_store.register_token("cop", "test-cop-token")
    default_store.register_token("thief", "test-thief-token")
    return path


async def _mock_llm(prompt: str) -> str:
    return json.dumps({"action": "stay", "nl_message": "I'll wait here."})


def test_full_game_six_valid_subgames(fast_config: Path) -> None:  # noqa: ARG001
    """Full 6-valid-sub-game loop with direct MCP and mocked LLM."""
    from cop_thief.shared.config import Config

    config = Config.from_env()
    sdk = CopThiefSDK(config, use_direct_mcp=True, llm_caller=_mock_llm)
    report = sdk.run_full_game()
    assert report.sub_games_played == 6
    assert len(report.result.sub_games) == 6
    assert all(sg.winner in (Outcome.COP_WIN, Outcome.THIEF_WIN) for sg in report.result.sub_games)
    assert report.cop_total > 0
    assert report.thief_total > 0


def test_technical_failure_rerun(fast_config: Path, monkeypatch: pytest.MonkeyPatch) -> None:  # noqa: ARG001
    """Forced failure on first sub-game attempt is retried; still 6 valid."""
    from cop_thief.shared.config import Config

    config = Config.from_env()
    sdk = CopThiefSDK(config, use_direct_mcp=True, llm_caller=_mock_llm)
    calls = {"n": 0}
    original = sdk._loop.run_sub_game  # noqa: SLF001

    async def flaky_run(index: int):  # noqa: ANN202
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("simulated technical failure")
        return await original(index)

    monkeypatch.setattr(sdk._loop, "run_sub_game", flaky_run)  # noqa: SLF001
    report = sdk.run_full_game()
    assert report.sub_games_played == 6
    assert calls["n"] > 6
