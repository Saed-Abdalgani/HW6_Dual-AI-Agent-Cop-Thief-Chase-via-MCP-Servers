"""Unit tests for MCP server tools."""

from __future__ import annotations

import pytest

from cop_thief.mcp_servers import _state, tools
from cop_thief.shared.auth import default_store


@pytest.fixture(autouse=True)
def clean_state(tmp_path: object, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirect state file to a temporary file per test."""
    from cop_thief.mcp_servers._state_backend import reset_state_backend

    test_state_file = tmp_path / "test_mcp_state.json"
    monkeypatch.setattr(_state, "STATE_PATH", test_state_file)
    monkeypatch.delenv("MCP_STATE_PATH", raising=False)
    reset_state_backend()
    if test_state_file.exists():
        test_state_file.unlink()
    yield
    reset_state_backend()
    if test_state_file.exists():
        test_state_file.unlink()


@pytest.fixture
def auth_tokens() -> tuple[str, str]:
    """Register and return fresh cop and thief tokens."""
    cop_tok = "test-tok-cop"
    thief_tok = "test-tok-thief"
    default_store.register_token("cop", cop_tok)
    default_store.register_token("thief", thief_tok)
    return cop_tok, thief_tok


class TestMcpTools:
    def test_messaging_happy_path(self, auth_tokens: tuple[str, str]) -> None:
        cop_tok, thief_tok = auth_tokens

        # Send messages
        r1 = tools.send_message("cop", "I see you!", cop_tok)
        assert r1["ok"] is True
        assert "msg_id" in r1

        r2 = tools.send_message("thief", "Catch me if you can!", thief_tok)
        assert r2["ok"] is True

        # Receive messages
        thief_rx = tools.receive_message("thief", thief_tok)
        assert thief_rx["text"] == "I see you!"

        cop_rx = tools.receive_message("cop", cop_tok)
        assert cop_rx["text"] == "Catch me if you can!"

    def test_update_and_verify_position(self, auth_tokens: tuple[str, str]) -> None:
        cop_tok, thief_tok = auth_tokens

        # Initial positions
        c_pos = tools.verify_position("cop", cop_tok)["pos"]
        assert c_pos == [0, 0]

        # Update position
        tools.update_position("cop", [1, 1], cop_tok)
        assert tools.verify_position("cop", cop_tok)["pos"] == [1, 1]

        # Out-of-bounds/blocked update should fail
        with pytest.raises(ValueError, match="blocked or out-of-bounds"):
            tools.update_position("cop", [-1, 0], cop_tok)

    def test_choose_action(self, auth_tokens: tuple[str, str]) -> None:
        cop_tok, _ = auth_tokens
        res = tools.choose_action("cop", {}, cop_tok)
        assert "action" in res
        assert isinstance(res["action"], str)

    def test_apply_action_turn_order_and_terminal(self, auth_tokens: tuple[str, str]) -> None:
        cop_tok, thief_tok = auth_tokens

        # Initial turn is thief's turn (as thief_moves_first=True by default)
        # Cop trying to move first should fail
        r_cop = tools.apply_action("cop", "down", cop_tok)
        assert r_cop["legal"] is False
        assert "Not your turn" in r_cop["rejection_reason"]

        # Thief moves legal action
        r_thief = tools.apply_action("thief", "up", thief_tok)
        assert r_thief["legal"] is True

        # Now it is Cop's turn
        r_cop_ok = tools.apply_action("cop", "down", cop_tok)
        assert r_cop_ok["legal"] is True

        # Test illegal action check
        r_bad = tools.apply_action("thief", "invalid_action", thief_tok)
        assert r_bad["legal"] is False

    def test_game_status_and_scores(self, auth_tokens: tuple[str, str]) -> None:
        cop_tok, _ = auth_tokens
        status = tools.game_status(cop_tok)
        assert status["over"] is False
        assert status["winner"] == "in_progress"
        assert status["scores"] == {"cop": 0, "thief": 0}  # starting/mid-game scores
