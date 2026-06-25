"""Game-wide constants for the Cop–Thief MCP system.

All magic strings and enumerations live here so the rest of the codebase
never duplicates or hard-codes them.

Traces: PLAN §9, T-P0-13.
"""

from __future__ import annotations

from enum import StrEnum, unique

# ---------------------------------------------------------------------------
# Agent identity
# ---------------------------------------------------------------------------


@unique
class Agent(StrEnum):
    """Identifies one of the two players."""

    COP = "cop"
    THIEF = "thief"


# ---------------------------------------------------------------------------
# Action vocabulary
# ---------------------------------------------------------------------------


@unique
class Action(StrEnum):
    """All legal actions an agent may request on its turn.

    Orthogonal + diagonal moves, a no-op stay, and the cop-exclusive
    ``place_barrier`` action.
    """

    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    UP_LEFT = "up_left"
    UP_RIGHT = "up_right"
    DOWN_LEFT = "down_left"
    DOWN_RIGHT = "down_right"
    STAY = "stay"
    PLACE_BARRIER = "place_barrier"


# Subset of actions available to the thief (excludes place_barrier).
THIEF_ACTIONS: frozenset[Action] = frozenset(a for a in Action if a is not Action.PLACE_BARRIER)

# All actions available to the cop.
COP_ACTIONS: frozenset[Action] = frozenset(Action)

# Movement delta (row, col) for each directional action.
MOVE_DELTAS: dict[Action, tuple[int, int]] = {
    Action.UP: (-1, 0),
    Action.DOWN: (1, 0),
    Action.LEFT: (0, -1),
    Action.RIGHT: (0, 1),
    Action.UP_LEFT: (-1, -1),
    Action.UP_RIGHT: (-1, 1),
    Action.DOWN_LEFT: (1, -1),
    Action.DOWN_RIGHT: (1, 1),
    Action.STAY: (0, 0),
}


# ---------------------------------------------------------------------------
# Game outcome labels
# ---------------------------------------------------------------------------


@unique
class Outcome(StrEnum):
    """Terminal outcome of a sub-game."""

    COP_WIN = "cop_win"
    THIEF_WIN = "thief_win"
    IN_PROGRESS = "in_progress"
    TECHNICAL_FAILURE = "technical_failure"


# ---------------------------------------------------------------------------
# Strategy identifiers
# ---------------------------------------------------------------------------


@unique
class Strategy(StrEnum):
    """Selectable decision strategies (matches config ``strategy`` values)."""

    HEURISTIC = "heuristic"
    QLEARNING = "qlearning"
    LLM = "llm"


# ---------------------------------------------------------------------------
# Start-mode identifiers
# ---------------------------------------------------------------------------


@unique
class StartMode(StrEnum):
    """How initial agent positions are chosen at the start of a sub-game."""

    RANDOM = "random"
    STRATEGY = "strategy"


# ---------------------------------------------------------------------------
# Misc defaults (all overridable via config)
# ---------------------------------------------------------------------------

DEFAULT_GRID_SIZE: tuple[int, int] = (5, 5)
DEFAULT_MAX_MOVES: int = 25
DEFAULT_NUM_GAMES: int = 6
DEFAULT_MAX_BARRIERS: int = 5
