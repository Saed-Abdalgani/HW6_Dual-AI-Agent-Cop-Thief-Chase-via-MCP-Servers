"""Opponent position belief from move history (pre-NL stub).

Refined in Phase P5 with NL parsing.  Traces: FR-NL2, PLAN §14, T-P3-12.
"""

from __future__ import annotations

from cop_thief.constants import MOVE_DELTAS, Action, Agent
from cop_thief.services.orchestrator._types import Observation


class OpponentEstimator:
    """Maintain a coarse belief over the opponent's grid cell."""

    def __init__(self, grid_size: tuple[int, int]) -> None:
        """Start with the grid centre as the initial belief."""
        self._grid = grid_size
        self._belief: tuple[int, int] = (grid_size[0] // 2, grid_size[1] // 2)

    @property
    def estimate(self) -> tuple[int, int]:
        """Current best-guess opponent position."""
        return self._belief

    def update_from_message(self, text: str) -> None:
        """Stub: nudge belief toward mentioned compass directions."""
        if not text:
            return
        lower = text.lower()
        r, c = self._belief
        rows, cols = self._grid
        if "north" in lower or "up" in lower:
            r = max(0, r - 1)
        if "south" in lower or "down" in lower:
            r = min(rows - 1, r + 1)
        if "west" in lower or "left" in lower:
            c = max(0, c - 1)
        if "east" in lower or "right" in lower:
            c = min(cols - 1, c + 1)
        self._belief = (r, c)

    def update_from_action(self, agent: Agent, action: Action, own_pos: tuple[int, int]) -> None:
        """Shift belief when we observe our own move (no direct opponent view)."""
        if agent is Agent.COP:
            dr, dc = MOVE_DELTAS.get(action, (0, 0))
            nr, nc = own_pos[0] - dr, own_pos[1] - dc
            rows, cols = self._grid
            if 0 <= nr < rows and 0 <= nc < cols:
                self._belief = (nr, nc)

    def for_agent(self, agent: Agent, own_pos: tuple[int, int]) -> tuple[int, int]:
        """Return opponent estimate relative to *agent*."""
        if agent is Agent.COP:
            return self._belief
        # Thief estimates cop as mirror of belief when cop moved toward thief
        return self._belief

    def reset(self, cop_pos: tuple[int, int], thief_pos: tuple[int, int]) -> None:
        """Reset beliefs at sub-game start (cop sees thief estimate, vice versa)."""
        self._belief = thief_pos  # cop's estimate of thief
        self._cop_estimate = cop_pos

    def estimate_for(self, agent: Agent) -> tuple[int, int]:
        """Return opponent position estimate for *agent*."""
        if agent is Agent.COP:
            return self._belief
        return getattr(self, "_cop_estimate", (0, 0))

    def build_observation(
        self,
        agent: Agent,
        own_pos: tuple[int, int],
        barriers: frozenset[tuple[int, int]],
        barriers_used: int,
        max_barriers: int,
        move_count: int,
        last_message: str,
    ) -> Observation:
        """Build an :class:`Observation` for strategy / LLM."""
        return Observation(
            agent=agent,
            own_pos=own_pos,
            opp_estimate=self.estimate_for(agent),
            barriers=barriers,
            barriers_used=barriers_used,
            max_barriers=max_barriers,
            grid_size=self._grid,
            move_count=move_count,
            last_message=last_message,
        )
