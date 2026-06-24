"""SDK live-frame callback integration tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cop_thief.mcp_servers import _state
from cop_thief.sdk.facade import CopThiefSDK
from cop_thief.shared.config import Config


async def _mock_llm(_prompt: str) -> str:
    return json.dumps({"action": "stay", "nl_message": "waiting"})


def test_run_sub_game_emits_live_frames(
    valid_config_yaml: Path,
    minimal_env: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("CONFIG_PATH", str(valid_config_yaml))
    monkeypatch.setattr(_state, "STATE_PATH", tmp_path / "mcp_state.json")
    config = Config.from_env()
    frames = []
    sdk = CopThiefSDK(config, use_direct_mcp=True, llm_caller=_mock_llm)

    result = sdk.run_sub_game(on_frame=frames.append)

    assert result.moves_used > 0
    assert frames
    assert frames[0].grid_size == config.grid_size
