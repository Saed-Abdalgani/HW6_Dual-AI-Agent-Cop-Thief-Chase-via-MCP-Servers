"""Barrier-placement relocation helper.

Keeps :mod:`rules` focused on rule orchestration while preserving the PRD
invariant that agents do not occupy barrier cells.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cop_thief.constants import MOVE_DELTAS, Action

if TYPE_CHECKING:
    from cop_thief.services.engine.board import Board


def relocation_after_barrier(board: Board, current_pos: tuple[int, int]) -> tuple[int, int] | None:
    """Return the first adjacent cell that preserves barrier invariants."""
    occupied = {board.thief_pos}
    blocked = board.barriers | frozenset([current_pos])
    for action, delta in MOVE_DELTAS.items():
        if action is Action.STAY:
            continue
        candidate = (current_pos[0] + delta[0], current_pos[1] + delta[1])
        if board.in_bounds(candidate) and candidate not in blocked and candidate not in occupied:
            return candidate
    return None
