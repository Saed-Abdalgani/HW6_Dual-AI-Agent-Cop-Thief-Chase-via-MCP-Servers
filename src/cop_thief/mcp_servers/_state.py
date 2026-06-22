"""Helper module for state management in MCP servers.

Manages loading, saving, and converting the JSON state to/from engine objects.
Traces: T-P2-08, T-P7-02, T-P7-03.
"""

from __future__ import annotations

from pathlib import Path

from cop_thief.constants import Outcome
from cop_thief.mcp_servers._state_backend import get_state_backend, reset_state_backend
from cop_thief.services.engine._turn_state import TurnState
from cop_thief.services.engine.board import Board
from cop_thief.services.engine.rules import RuleEngine
from cop_thief.shared.config import Config

STATE_PATH = Path("data/mcp_state.json")


def load_state() -> dict:
    """Load JSON game state, initializing if absent or corrupt."""
    backend = get_state_backend(STATE_PATH)
    stored = backend.read()
    if stored is not None:
        return stored
    config = Config.from_env()
    state = {
        "cop_pos": [0, 0],
        "thief_pos": [config.grid_size[0] - 1, config.grid_size[1] - 1],
        "barriers": [],
        "barriers_used": 0,
        "messages": [],
        "round_number": 0,
        "awaiting_second": False,
        "over": False,
        "winner": "in_progress",
    }
    save_state(state)
    return state


def save_state(state: dict) -> None:
    """Save game state through the configured backend."""
    get_state_backend(STATE_PATH).write(state)


def clear_state_file() -> None:
    """Remove local state and reset the backend cache."""
    reset_state_backend()
    STATE_PATH.unlink(missing_ok=True)


def get_engine_objects(state: dict) -> tuple[Board, TurnState, RuleEngine]:
    """Rebuild engine objects from stored state."""
    config = Config.from_env()
    board = Board(rows=config.grid_size[0], cols=config.grid_size[1])
    board.cop_pos = tuple(state["cop_pos"])
    board.thief_pos = tuple(state["thief_pos"])
    board.barriers = frozenset(tuple(b) for b in state["barriers"])
    board.barriers_used = state["barriers_used"]
    turn = TurnState(thief_moves_first=config.thief_moves_first)
    turn.round_number = state["round_number"]
    turn._awaiting_second = state["awaiting_second"]
    rules = RuleEngine(max_barriers=config.max_barriers, max_moves=config.max_moves)
    return board, turn, rules


def update_state_from_engine(state: dict, board: Board, turn: TurnState, rules: RuleEngine) -> None:
    """Sync state dict with updated engine objects."""
    state["cop_pos"] = list(board.cop_pos)
    state["thief_pos"] = list(board.thief_pos)
    state["barriers"] = [list(b) for b in board.barriers]
    state["barriers_used"] = board.barriers_used
    state["round_number"] = turn.round_number
    state["awaiting_second"] = turn._awaiting_second
    outcome = rules.check_terminal(board, turn)
    if outcome is not Outcome.IN_PROGRESS:
        state["over"] = True
        state["winner"] = outcome.value
    else:
        state["over"] = False
        state["winner"] = "in_progress"
