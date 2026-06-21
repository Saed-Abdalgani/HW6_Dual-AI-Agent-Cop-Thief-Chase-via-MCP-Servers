"""TurnState — tracks which agent acts next within a sub-game round.

Factored out of :mod:`.rules` to keep each module under ~150 LOC.

Traces: FR-M5, T-P1-09.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cop_thief.constants import Agent


@dataclass
class TurnState:
    """Mutable turn-order tracker for one sub-game.

    Args:
        thief_moves_first: When ``True`` (default) the thief acts before the
            cop in each round.

    """

    thief_moves_first: bool = True
    round_number: int = field(default=0, init=False)
    _first_in_round: Agent = field(init=False)
    _second_in_round: Agent = field(init=False)
    _awaiting_second: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        """Set the per-round agent order based on *thief_moves_first*."""
        if self.thief_moves_first:
            self._first_in_round = Agent.THIEF
            self._second_in_round = Agent.COP
        else:
            self._first_in_round = Agent.COP
            self._second_in_round = Agent.THIEF

    @property
    def current_agent(self) -> Agent:
        """The agent whose turn it is right now."""
        return self._second_in_round if self._awaiting_second else self._first_in_round

    def advance(self) -> None:
        """Advance to the next half-turn; increment round on completion."""
        if self._awaiting_second:
            self._awaiting_second = False
            self.round_number += 1
        else:
            self._awaiting_second = True
