"""Accumulate sub-game results and running totals.

Traces: FR-S2, PLAN §10.4, T-P3-11.
"""

from __future__ import annotations

from cop_thief.services.engine._lifecycle_types import FullGameResult, SubGameResult
from cop_thief.services.engine.scoring import ScoreTotals


class ResultCollector:
    """Wrap :class:`FullGameResult` with orchestrator-friendly helpers."""

    def __init__(self) -> None:
        """Start with an empty collection."""
        self._result = FullGameResult()

    @property
    def sub_games(self) -> list[SubGameResult]:
        """Recorded valid sub-games."""
        return self._result.sub_games

    @property
    def totals(self) -> ScoreTotals:
        """Cumulative scores."""
        return self._result.totals

    @property
    def count(self) -> int:
        """Number of valid sub-games collected."""
        return len(self._result.sub_games)

    def add(self, result: SubGameResult) -> None:
        """Record a valid sub-game result."""
        self._result.add(result)

    def to_full_result(self) -> FullGameResult:
        """Return the underlying :class:`FullGameResult`."""
        return self._result
