"""Game engine public API.

Re-exports main classes and functions from the engine submodules so callers
can import directly from ``cop_thief.services.engine``.

Traces: PLAN §6, T-P1-02..T-P1-19.
"""

from cop_thief.services.engine._lifecycle_types import FullGameResult, SubGameResult
from cop_thief.services.engine._move_result import MoveResult
from cop_thief.services.engine._sub_game_runner import AgentDecider, run_sub_game
from cop_thief.services.engine._turn_state import TurnState
from cop_thief.services.engine.board import Board
from cop_thief.services.engine.lifecycle import run_full_game
from cop_thief.services.engine.rules import RuleEngine
from cop_thief.services.engine.scoring import ScoreTotals, SubGameScore, calculate_score

__all__ = [
    "AgentDecider",
    "Board",
    "FullGameResult",
    "MoveResult",
    "RuleEngine",
    "ScoreTotals",
    "SubGameResult",
    "SubGameScore",
    "TurnState",
    "calculate_score",
    "run_full_game",
    "run_sub_game",
]
