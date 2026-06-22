"""SDK facade types for public API responses.

Traces: PLAN §7, §10.4, T-P3-13.
"""

from __future__ import annotations

from dataclasses import dataclass

from cop_thief.services.engine._lifecycle_types import FullGameResult
from cop_thief.services.orchestrator._types import GameState, HealthStatus

__all__ = ["FullGameReport", "GameState", "HealthStatus"]


@dataclass
class FullGameReport:
    """Result of :meth:`CopThiefSDK.run_full_game`."""

    result: FullGameResult
    sub_games_played: int = 0
    cop_total: int = 0
    thief_total: int = 0
    message: str = ""

    @classmethod
    def from_result(cls, result: FullGameResult) -> FullGameReport:
        """Build a report wrapper from a :class:`FullGameResult`."""
        return cls(
            result=result,
            sub_games_played=len(result.sub_games),
            cop_total=result.totals.cop,
            thief_total=result.totals.thief,
            message="Full game complete.",
        )
