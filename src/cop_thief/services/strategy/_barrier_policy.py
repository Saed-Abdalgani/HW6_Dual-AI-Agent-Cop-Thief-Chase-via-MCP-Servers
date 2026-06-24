"""Shared strategy checks for barrier-placement feasibility."""

from __future__ import annotations

from cop_thief.constants import MOVE_DELTAS, Action, Agent
from cop_thief.services.orchestrator._types import Observation


def can_place_barrier(obs: Observation) -> bool:
    """Return True when a cop barrier action is worth proposing."""
    if obs.agent is not Agent.COP:
        return False
    if obs.barriers_used >= obs.max_barriers or obs.own_pos in obs.barriers:
        return False
    return _has_relocation_candidate(obs)


def _has_relocation_candidate(obs: Observation) -> bool:
    occupied_estimates = {obs.opp_estimate}
    blocked = obs.barriers | frozenset([obs.own_pos])
    rows, cols = obs.grid_size
    for action, delta in MOVE_DELTAS.items():
        if action is Action.STAY:
            continue
        candidate = (obs.own_pos[0] + delta[0], obs.own_pos[1] + delta[1])
        if (
            0 <= candidate[0] < rows
            and 0 <= candidate[1] < cols
            and candidate not in blocked
            and candidate not in occupied_estimates
        ):
            return True
    return False
