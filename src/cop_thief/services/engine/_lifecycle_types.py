"""Result dataclasses for sub-game and full-game lifecycles.

Factored out of :mod:`.lifecycle` to keep each file under ~150 LOC.

Traces: FR-L1, FR-L2, FR-S2, PLAN §10.4, T-P1-17, T-P1-18.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from cop_thief.constants import Outcome
from cop_thief.services.engine.scoring import ScoreTotals, SubGameScore

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class SubGameResult:
    """Result of a single completed sub-game.

    Attributes:
        index: 1-based index of this sub-game in the full game.
        winner: Terminal outcome (``COP_WIN`` or ``THIEF_WIN``).
        moves_used: Number of complete rounds played.
        barriers_used: Number of barriers placed by the cop.
        score: Points awarded to each agent.

    """

    index: int
    winner: Outcome
    moves_used: int
    barriers_used: int
    score: SubGameScore


@dataclass
class FullGameResult:
    """Aggregated result of a complete *num_games*-sub-game session.

    Attributes:
        sub_games: Ordered list of valid sub-game results.
        totals: Cumulative scores across all sub-games.

    """

    sub_games: list[SubGameResult] = field(default_factory=list)
    totals: ScoreTotals = field(default_factory=ScoreTotals)

    def add(self, result: SubGameResult) -> None:
        """Append *result* and update totals.

        Args:
            result: A valid :class:`SubGameResult` to record.

        """
        self.sub_games.append(result)
        self.totals.add(result.score)
