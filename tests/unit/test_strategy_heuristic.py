"""Unit tests for Manhattan heuristic strategy."""

from __future__ import annotations

from cop_thief.constants import Action, Agent
from cop_thief.services.orchestrator._types import Observation
from cop_thief.services.strategy.heuristic import choose_heuristic_action


def _obs(
    agent: Agent,
    own: tuple[int, int],
    opp: tuple[int, int],
    *,
    barriers_used: int = 0,
    max_barriers: int = 5,
    barriers: frozenset[tuple[int, int]] = frozenset(),
    grid_size: tuple[int, int] = (5, 5),
) -> Observation:
    return Observation(
        agent=agent,
        own_pos=own,
        opp_estimate=opp,
        barriers=barriers,
        barriers_used=barriers_used,
        max_barriers=max_barriers,
        grid_size=grid_size,
        move_count=0,
    )


def _dist(own: tuple[int, int], opp: tuple[int, int], action: Action) -> int:
    from cop_thief.constants import MOVE_DELTAS

    dr, dc = MOVE_DELTAS[action]
    return abs(own[0] + dr - opp[0]) + abs(own[1] + dc - opp[1])


def test_cop_reduces_manhattan_distance() -> None:
    own, opp = (2, 2), (0, 0)
    action = choose_heuristic_action(_obs(Agent.COP, own, opp))
    assert _dist(own, opp, action) <= abs(own[0] - opp[0]) + abs(own[1] - opp[1])


def test_thief_increases_manhattan_distance() -> None:
    own, opp = (2, 2), (0, 0)
    action = choose_heuristic_action(_obs(Agent.THIEF, own, opp))
    assert _dist(own, opp, action) >= abs(own[0] - opp[0]) + abs(own[1] - opp[1])


def test_cop_places_barrier_when_adjacent_and_budget() -> None:
    action = choose_heuristic_action(_obs(Agent.COP, (1, 0), (0, 0)))
    assert action is Action.PLACE_BARRIER


def test_barrier_blocked_when_budget_exhausted() -> None:
    action = choose_heuristic_action(
        _obs(Agent.COP, (1, 0), (0, 0), barriers_used=5, max_barriers=5),
    )
    assert action is not Action.PLACE_BARRIER


def test_cop_does_not_place_duplicate_barrier() -> None:
    action = choose_heuristic_action(
        _obs(Agent.COP, (1, 0), (0, 0), barriers=frozenset({(1, 0)})),
    )
    assert action is not Action.PLACE_BARRIER


def test_cop_skips_barrier_when_no_relocation_candidate() -> None:
    barriers = frozenset({(0, 1), (1, 0), (1, 1)})
    action = choose_heuristic_action(
        _obs(Agent.COP, (0, 0), (0, 1), barriers=barriers, grid_size=(2, 2)),
    )
    assert action is not Action.PLACE_BARRIER


def test_uses_estimate_not_ground_truth() -> None:
    """Strategy keys off opp_estimate; ground truth is not in Observation."""
    own = (2, 2)
    estimate_far = (4, 4)
    action = choose_heuristic_action(_obs(Agent.COP, own, estimate_far))
    assert _dist(own, estimate_far, action) <= 4
