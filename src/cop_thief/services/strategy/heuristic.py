"""Manhattan-distance heuristic baseline strategy.

Used as config-selectable strategy (P4) and LLM fallback (P3).

Traces: FR-D1, PLAN §14, T-P3-05, T-P4-03.
"""

from __future__ import annotations

from cop_thief.constants import COP_ACTIONS, MOVE_DELTAS, THIEF_ACTIONS, Action, Agent
from cop_thief.services.orchestrator._types import Observation


def _manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _legal_moves(obs: Observation) -> list[Action]:
    """Return movement actions that land on an in-bounds, unblocked cell."""
    r, c = obs.own_pos
    actions = THIEF_ACTIONS if obs.agent is Agent.THIEF else COP_ACTIONS
    legal: list[Action] = []
    for act in actions:
        if act is Action.PLACE_BARRIER:
            continue
        dr, dc = MOVE_DELTAS[act]
        tgt = (r + dr, c + dc)
        rows, cols = obs.grid_size
        if 0 <= tgt[0] < rows and 0 <= tgt[1] < cols and tgt not in obs.barriers:
            legal.append(act)
    return legal or [Action.STAY]


def choose_heuristic_action(obs: Observation) -> Action:
    """Pick an action using Manhattan distance to the opponent estimate."""
    legal = _legal_moves(obs)
    opp = obs.opp_estimate

    if (
        obs.agent is Agent.COP
        and Action.PLACE_BARRIER in COP_ACTIONS
        and obs.barriers_used < obs.max_barriers
        and _manhattan(obs.own_pos, opp) <= 1
    ):
        return Action.PLACE_BARRIER

    if obs.agent is Agent.COP:
        return min(legal, key=lambda a: _manhattan(_target(obs, a), opp))
    return max(legal, key=lambda a: _manhattan(_target(obs, a), opp))


def _target(obs: Observation, action: Action) -> tuple[int, int]:
    dr, dc = MOVE_DELTAS[action]
    r, c = obs.own_pos
    return (r + dr, c + dc)
