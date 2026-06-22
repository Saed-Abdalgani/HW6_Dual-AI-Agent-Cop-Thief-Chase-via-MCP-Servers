"""Local turn-order tracker mirroring engine :class:`TurnState`.

Traces: FR-M5, T-P3-07.
"""

from __future__ import annotations

from cop_thief.constants import Agent


class TurnTracker:
    """Track thief-first alternating turns for the orchestrator."""

    def __init__(self, thief_moves_first: bool = True) -> None:
        """Initialize with configured turn order."""
        self._thief_first = thief_moves_first
        self._awaiting_second = False
        self.round_number = 0

    @property
    def current_agent(self) -> Agent:
        """Agent whose turn it is right now."""
        if not self._awaiting_second:
            return Agent.THIEF if self._thief_first else Agent.COP
        return Agent.COP if self._thief_first else Agent.THIEF

    def advance(self) -> None:
        """Advance to the next agent or next round."""
        if not self._awaiting_second:
            self._awaiting_second = True
        else:
            self._awaiting_second = False
            self.round_number += 1

    def reset(self) -> None:
        """Reset for a new sub-game."""
        self._awaiting_second = False
        self.round_number = 0
