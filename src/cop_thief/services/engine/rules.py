"""Game rules: move resolution, legality checks, and victory detection.

Imports :class:`MoveResult` from :mod:`._move_result` and
:class:`TurnState` from :mod:`._turn_state` to stay under ~150 LOC.

Traces: FR-M1..M5, FR-BR1..BR5, FR-V1..V3, T-P1-06..T-P1-14.
"""

from __future__ import annotations

import logging

from cop_thief.constants import COP_ACTIONS, MOVE_DELTAS, THIEF_ACTIONS, Action, Agent, Outcome
from cop_thief.services.engine._move_result import MoveResult
from cop_thief.services.engine._turn_state import TurnState
from cop_thief.services.engine.board import Board

# Re-export so existing imports from rules work unchanged.
__all__ = ["MoveResult", "RuleEngine", "TurnState"]

logger = logging.getLogger(__name__)


class RuleEngine:
    """Applies game rules to a :class:`Board` and returns move results.

    Args:
        max_barriers: Maximum barriers the cop may place per sub-game.
        max_moves: Maximum rounds before thief wins by escape.

    """

    def __init__(self, max_barriers: int, max_moves: int) -> None:
        """Initialise with per-game limits from config."""
        self.max_barriers = max_barriers
        self.max_moves = max_moves

    def apply_action(self, board: Board, agent: Agent, action: Action) -> MoveResult:
        """Validate and apply *action* for *agent* on *board*.

        Args:
            board: Current board state (mutated in-place on success).
            agent: The agent taking the action.
            action: The requested action.

        Returns:
            A :class:`MoveResult` describing the outcome.

        """
        current_pos = board.get_pos(agent)

        if agent is Agent.THIEF and action not in THIEF_ACTIONS:
            reason = f"Thief cannot perform action '{action}'."
            logger.warning("Rejected %s action for %s: %s", action, agent, reason)
            return MoveResult(legal=False, new_pos=current_pos, rejection_reason=reason)

        if agent is Agent.COP and action not in COP_ACTIONS:
            reason = f"Cop cannot perform action '{action}'."
            logger.warning("Rejected %s action for %s: %s", action, agent, reason)
            return MoveResult(legal=False, new_pos=current_pos, rejection_reason=reason)

        if action is Action.PLACE_BARRIER:
            return self._handle_place_barrier(board, agent, current_pos)

        return self._handle_movement(board, agent, action, current_pos)

    def check_terminal(self, board: Board, turn_state: TurnState) -> Outcome:
        """Return the terminal outcome for the current board + turn state.

        Args:
            board: Current board state.
            turn_state: Current turn / round tracker.

        Returns:
            ``COP_WIN``, ``THIEF_WIN``, or ``IN_PROGRESS``.

        """
        if board.cop_pos == board.thief_pos:
            return Outcome.COP_WIN
        if turn_state.round_number >= self.max_moves:
            return Outcome.THIEF_WIN
        return Outcome.IN_PROGRESS

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _handle_place_barrier(
        self, board: Board, agent: Agent, current_pos: tuple[int, int]
    ) -> MoveResult:
        """Execute or reject a ``place_barrier`` action."""
        if agent is not Agent.COP:
            reason = "Only the cop may place barriers."
            logger.warning("Rejected place_barrier for %s: %s", agent, reason)
            return MoveResult(legal=False, new_pos=current_pos, rejection_reason=reason)

        if board.barriers_used >= self.max_barriers:
            reason = f"Barrier budget exhausted ({board.barriers_used}/{self.max_barriers})."
            logger.warning("Rejected place_barrier for cop: %s", reason)
            return MoveResult(legal=False, new_pos=current_pos, rejection_reason=reason)

        board.place_barrier(current_pos)
        logger.debug(
            "Cop placed barrier at %s (%d/%d).",
            current_pos,
            board.barriers_used,
            self.max_barriers,
        )
        return MoveResult(legal=True, new_pos=current_pos, barrier_placed=True)

    def _handle_movement(
        self, board: Board, agent: Agent, action: Action, current_pos: tuple[int, int]
    ) -> MoveResult:
        """Execute or reject a directional/stay move."""
        delta = MOVE_DELTAS[action]
        target = (current_pos[0] + delta[0], current_pos[1] + delta[1])

        if not board.in_bounds(target):
            reason = f"Target {target} is outside the grid."
            logger.warning("Rejected move %s for %s: %s", action, agent, reason)
            return MoveResult(legal=False, new_pos=current_pos, rejection_reason=reason)

        if board.is_blocked(target):
            reason = f"Target {target} is a barrier."
            logger.warning("Rejected move %s for %s: %s", action, agent, reason)
            return MoveResult(legal=False, new_pos=current_pos, rejection_reason=reason)

        board.set_pos(agent, target)
        logger.debug("%s moved %s → %s.", agent, action, target)

        if board.cop_pos == board.thief_pos:
            return MoveResult(legal=True, new_pos=target, outcome=Outcome.COP_WIN)

        return MoveResult(legal=True, new_pos=target)
