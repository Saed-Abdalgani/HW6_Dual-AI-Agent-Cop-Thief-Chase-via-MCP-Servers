"""Unit tests for shared MCP state backends."""

from __future__ import annotations

import json

import pytest

from cop_thief.mcp_servers._state_backend import (
    FileStateBackend,
    get_state_backend,
    reset_state_backend,
)


def test_file_state_backend_round_trip(tmp_path: object) -> None:
    path = tmp_path / "state.json"  # type: ignore[operator]
    backend = FileStateBackend(path)
    payload = {"cop_pos": [1, 1], "thief_pos": [3, 3]}
    backend.write(payload)
    assert backend.read() == payload


def test_get_state_backend_uses_env_path(
    tmp_path: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "env_state.json"  # type: ignore[operator]
    monkeypatch.setenv("MCP_STATE_PATH", str(path))
    reset_state_backend()
    backend = get_state_backend(path.parent / "ignored.json")
    backend.write({"winner": "in_progress"})
    assert json.loads(path.read_text(encoding="utf-8"))["winner"] == "in_progress"
