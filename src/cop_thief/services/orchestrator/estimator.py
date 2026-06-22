"""Opponent position belief from move history and NL cues.

Traces: FR-NL2, FR-NL3, PLAN §14, T-P3-12, T-P5-05, T-P5-06.
"""

from __future__ import annotations

from cop_thief.constants import MOVE_DELTAS, Action, Agent
from cop_thief.services.nlp.parser import ParsedMessage, cue_target, parse_message
from cop_thief.services.orchestrator._types import Observation


class OpponentEstimator:
    """Maintain per-agent coarse beliefs over the opponent's grid cell."""

    def __init__(self, grid_size: tuple[int, int]) -> None:
        """Start with the grid centre as the initial belief."""
        self._grid = grid_size
        center = (grid_size[0] // 2, grid_size[1] // 2)
        self._beliefs: dict[Agent, tuple[int, int]] = {
            Agent.COP: center,
            Agent.THIEF: center,
        }
        self._uncertainty: dict[Agent, float] = {Agent.COP: 1.0, Agent.THIEF: 1.0}
        self._last_cue: dict[Agent, ParsedMessage | None] = {
            Agent.COP: None,
            Agent.THIEF: None,
        }

    @property
    def estimate(self) -> tuple[int, int]:
        """Current cop-side best guess of the thief position."""
        return self._beliefs[Agent.COP]

    def uncertainty_for(self, agent: Agent) -> float:
        """Return uncertainty in the opponent estimate for *agent*."""
        return self._uncertainty[agent]

    def update_from_message(self, text: str, receiver: Agent = Agent.COP) -> ParsedMessage:
        """Fuse a free-text message into the receiver's opponent belief."""
        parsed = parse_message(text)
        self._last_cue[receiver] = parsed
        if parsed.ambiguous:
            self._uncertainty[receiver] = min(1.0, self._uncertainty[receiver] + 0.15)
            return parsed
        current = self._beliefs[receiver]
        target = cue_target(parsed, self._grid, current)
        self._beliefs[receiver] = self._blend(current, target, parsed.confidence)
        self._uncertainty[receiver] = max(0.1, 1.0 - parsed.confidence)
        return parsed

    def update_from_action(
        self,
        agent: Agent,
        action: Action,
        new_pos: tuple[int, int] | None = None,
    ) -> None:
        """Fuse observed move history into both agents' coarse beliefs."""
        if new_pos is None:
            return
        observer = Agent.THIEF if agent is Agent.COP else Agent.COP
        self._beliefs[observer] = self._clamp(new_pos)
        self._uncertainty[observer] = max(0.05, self._uncertainty[observer] - 0.2)
        self._drift_other_belief(agent, action)

    def for_agent(self, agent: Agent, own_pos: tuple[int, int]) -> tuple[int, int]:
        """Return opponent estimate relative to *agent*."""
        return self.estimate_for(agent)

    def reset(self, cop_pos: tuple[int, int], thief_pos: tuple[int, int]) -> None:
        """Reset beliefs at sub-game start (cop sees thief estimate, vice versa)."""
        self._beliefs[Agent.COP] = thief_pos
        self._beliefs[Agent.THIEF] = cop_pos
        self._uncertainty = {Agent.COP: 0.1, Agent.THIEF: 0.1}
        self._last_cue = {Agent.COP: None, Agent.THIEF: None}

    def estimate_for(self, agent: Agent) -> tuple[int, int]:
        """Return opponent position estimate for *agent*."""
        return self._beliefs[agent]

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

    def _blend(
        self,
        current: tuple[int, int],
        target: tuple[int, int],
        confidence: float,
    ) -> tuple[int, int]:
        weight = 0.75 if confidence >= 0.65 else 0.5
        r = round(current[0] * (1 - weight) + target[0] * weight)
        c = round(current[1] * (1 - weight) + target[1] * weight)
        return self._clamp((r, c))

    def _clamp(self, pos: tuple[int, int]) -> tuple[int, int]:
        rows, cols = self._grid
        return (min(max(pos[0], 0), rows - 1), min(max(pos[1], 0), cols - 1))

    def _drift_other_belief(self, agent: Agent, action: Action) -> None:
        if action is Action.PLACE_BARRIER:
            return
        dr, dc = MOVE_DELTAS.get(action, (0, 0))
        current = self._beliefs[agent]
        self._beliefs[agent] = self._clamp((current[0] + dr, current[1] + dc))
        self._uncertainty[agent] = min(1.0, self._uncertainty[agent] + 0.05)
