"""MoveResult — the outcome dataclass for a single agent action.

Factored out of :mod:`.rules` to keep each module under ~150 LOC.

Traces: T-P1-06, T-P1-07, T-P1-08, T-P1-10.
"""

from __future__ import annotations

from dataclasses import dataclass

from cop_thief.constants import Outcome


@dataclass(frozen=True)
class MoveResult:
    """Outcome of a single agent action.

    Attributes:
        legal: Whether the action was accepted.
        new_pos: Resulting position (unchanged if rejected).
        rejection_reason: Human-readable reason when *legal* is ``False``.
        barrier_placed: Whether a barrier was placed this turn.
        outcome: Terminal outcome if the move ended the sub-game, else ``None``.

    """

    legal: bool
    new_pos: tuple[int, int]
    rejection_reason: str | None = None
    barrier_placed: bool = False
    outcome: Outcome | None = None
