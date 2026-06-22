"""Client-side action legality checks before MCP apply.

Traces: PLAN §4, FR-MCP4, T-P3-08.
"""

from __future__ import annotations

from cop_thief.constants import COP_ACTIONS, MOVE_DELTAS, THIEF_ACTIONS, Action, Agent
from cop_thief.services.orchestrator._types import Observation


class ActionValidator:
    """Reject illegal moves and barrier placements client-side."""

    def is_legal(self, obs: Observation, action: Action) -> bool:
        """Return True when *action* is allowed for *obs*."""
        if obs.agent is Agent.THIEF and action not in THIEF_ACTIONS:
            return False
        if obs.agent is Agent.COP and action not in COP_ACTIONS:
            return False
        if action is Action.PLACE_BARRIER:
            return self._barrier_ok(obs)
        return self._move_ok(obs, action)

    def rejection_reason(self, obs: Observation, action: Action) -> str:
        """Human-readable reason when :meth:`is_legal` is False."""
        if not self.is_legal(obs, action):
            if action is Action.PLACE_BARRIER:
                return "Barrier not allowed (budget or agent)."
            return f"Move '{action}' is illegal from {obs.own_pos}."
        return ""

    def _barrier_ok(self, obs: Observation) -> bool:
        if obs.agent is not Agent.COP:
            return False
        return obs.barriers_used < obs.max_barriers

    def _move_ok(self, obs: Observation, action: Action) -> bool:
        dr, dc = MOVE_DELTAS[action]
        r, c = obs.own_pos
        tgt = (r + dr, c + dc)
        rows, cols = obs.grid_size
        if not (0 <= tgt[0] < rows and 0 <= tgt[1] < cols):
            return False
        return tgt not in obs.barriers
