"""Scoring module for Cop–Thief sub-games.

Calculates per-sub-game points from config and accumulates totals across
multiple sub-games.

Traces: FR-S1, FR-S2, FR-S3, PLAN §10.4, T-P1-15, T-P1-16.
"""

from __future__ import annotations

from dataclasses import dataclass

from cop_thief.constants import Outcome
from cop_thief.shared._config_schemas import ScoringConfig


@dataclass(frozen=True)
class SubGameScore:
    """Points awarded to each agent for one sub-game.

    Attributes:
        cop: Points awarded to the cop.
        thief: Points awarded to the thief.

    """

    cop: int
    thief: int


@dataclass
class ScoreTotals:
    """Cumulative scores across all valid sub-games.

    Attributes:
        cop: Total cop points.
        thief: Total thief points.
        sub_game_count: Number of valid sub-games accumulated.

    """

    cop: int = 0
    thief: int = 0
    sub_game_count: int = 0

    def add(self, score: SubGameScore) -> None:
        """Add *score* to the running totals.

        Args:
            score: Per-sub-game score to accumulate.

        """
        self.cop += score.cop
        self.thief += score.thief
        self.sub_game_count += 1


def calculate_score(outcome: Outcome, config: ScoringConfig) -> SubGameScore:
    """Return the points awarded for a sub-game with *outcome*.

    Args:
        outcome: The terminal outcome (``COP_WIN`` or ``THIEF_WIN``).
        config: The scoring config section from ``Config.scoring``.

    Returns:
        A :class:`SubGameScore` with points for each agent.

    Raises:
        ValueError: When *outcome* is not a terminal outcome.

    """
    if outcome is Outcome.COP_WIN:
        return SubGameScore(cop=config.cop_win, thief=config.thief_loss)
    if outcome is Outcome.THIEF_WIN:
        return SubGameScore(cop=config.cop_loss, thief=config.thief_win)
    msg = f"Cannot calculate score for non-terminal outcome: {outcome!r}."
    raise ValueError(msg)
