"""Manhattan-distance heuristic baseline strategy.

Uses opponent *estimate* (not ground truth) for distance calculations.

Traces: FR-D1, FR-NL2, PLAN §14, T-P3-05, T-P4-03..05.
"""

from __future__ import annotations

from cop_thief.constants import COP_ACTIONS, MOVE_DELTAS, THIEF_ACTIONS, Action, Agent
from cop_thief.services.orchestrator._types import Observation
from cop_thief.services.strategy._barrier_policy import can_place_barrier
from cop_thief.services.strategy.base import Strategy, StrategyDecision


def _manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _target(obs: Observation, action: Action) -> tuple[int, int]:
    dr, dc = MOVE_DELTAS[action]
    r, c = obs.own_pos
    return (r + dr, c + dc)


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
    """Pick an action using Manhattan distance to ``obs.opp_estimate``."""
    legal = _legal_moves(obs)
    opp = obs.opp_estimate

    if obs.agent is Agent.COP and can_place_barrier(obs) and _manhattan(obs.own_pos, opp) <= 1:
        return Action.PLACE_BARRIER

    if obs.agent is Agent.COP:
        return min(legal, key=lambda a: _manhattan(_target(obs, a), opp))
    return max(legal, key=lambda a: _manhattan(_target(obs, a), opp))


class HeuristicStrategy(Strategy):
    """Config-selectable heuristic strategy."""

    async def decide(self, obs: Observation) -> StrategyDecision:
        """Return Manhattan-based action and a short NL taunt."""
        action = choose_heuristic_action(obs)
        return StrategyDecision(action=action, nl_message="")

    def choose(self, obs: Observation) -> Action:
        """Return an action synchronously for fallback paths."""
        return choose_heuristic_action(obs)
