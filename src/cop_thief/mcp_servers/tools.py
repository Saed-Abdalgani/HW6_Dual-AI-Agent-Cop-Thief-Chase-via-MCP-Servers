"""Public facade for Cop and Thief MCP server tools.

The implementation lives in :mod:`cop_thief.mcp_servers._tools_impl` so server
modules can keep importing this stable public surface.
"""

from __future__ import annotations

from cop_thief.constants import Outcome
from cop_thief.mcp_servers._state import load_state
from cop_thief.mcp_servers._tools_impl import (
    apply_action,
    authorize,
    choose_action,
    receive_message,
    send_message,
    update_position,
    verify_position,
)
from cop_thief.services.engine.scoring import calculate_score
from cop_thief.shared.config import Config


def game_status(token: str) -> dict:
    """Get the current game status snapshot."""
    authorize(token)
    state = load_state()
    outcome_str = state["winner"]
    if outcome_str == "in_progress":
        scores = {"cop": 0, "thief": 0}
    else:
        config = Config.from_env()
        outcome = Outcome(outcome_str)
        score = calculate_score(outcome, config.scoring)
        scores = {"cop": score.cop, "thief": score.thief}
    return {
        "cop_pos": state["cop_pos"],
        "thief_pos": state["thief_pos"],
        "barriers": state["barriers"],
        "barriers_used": state["barriers_used"],
        "move_count": state["round_number"],
        "scores": scores,
        "over": state["over"],
        "winner": state["winner"],
    }

__all__ = [
    "apply_action",
    "authorize",
    "choose_action",
    "game_status",
    "receive_message",
    "send_message",
    "update_position",
    "verify_position",
]
