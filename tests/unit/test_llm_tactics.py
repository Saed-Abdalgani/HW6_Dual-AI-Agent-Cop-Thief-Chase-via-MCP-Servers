"""Unit tests for LLM tactical analysis."""

from __future__ import annotations

from cop_thief.constants import Action, Agent
from cop_thief.services.orchestrator._llm_tactics import build_tactical_brief, rank_actions
from cop_thief.services.orchestrator._types import Observation


def test_cop_prefers_capture_on_estimate_cell() -> None:
    obs = Observation(
        agent=Agent.COP,
        own_pos=(2, 2),
        opp_estimate=(2, 3),
        barriers=frozenset(),
        barriers_used=0,
        max_barriers=5,
        grid_size=(5, 5),
        move_count=3,
    )
    top = rank_actions(obs, top_n=1)[0]
    assert top.action is Action.RIGHT
    assert "capture" in top.reason


def test_cop_suggests_barrier_when_adjacent_and_not_closing() -> None:
    obs = Observation(
        agent=Agent.COP,
        own_pos=(2, 2),
        opp_estimate=(2, 3),
        barriers=frozenset({(2, 3)}),
        barriers_used=0,
        max_barriers=5,
        grid_size=(5, 5),
        move_count=3,
    )
    hints = rank_actions(obs)
    actions = {hint.action for hint in hints}
    assert Action.PLACE_BARRIER in actions


def test_thief_opens_distance_from_cop_estimate() -> None:
    obs = Observation(
        agent=Agent.THIEF,
        own_pos=(4, 4),
        opp_estimate=(4, 5),
        barriers=frozenset(),
        barriers_used=0,
        max_barriers=5,
        grid_size=(9, 9),
        move_count=10,
    )
    top = rank_actions(obs, top_n=1)[0]
    assert top.action is not Action.STAY
    assert "minimize U" in top.reason or "maximin" in top.reason or "maximin" in top.reason


def test_thief_prefers_interior_over_edge_flight_on_9x9() -> None:
    """APF wall repulsion should favor interior when cop threat is moderate."""
    obs = Observation(
        agent=Agent.THIEF,
        own_pos=(4, 4),
        opp_estimate=(4, 5),
        barriers=frozenset(),
        barriers_used=0,
        max_barriers=5,
        grid_size=(9, 9),
        move_count=3,
    )
    top = rank_actions(obs, top_n=1)[0]
    from cop_thief.services.orchestrator._llm_tactics import action_target, border_distance

    assert top.action is not Action.STAY
    assert border_distance(action_target(obs, top.action), 9, 9) >= 1


def test_thief_brief_includes_apf_and_must_move() -> None:
    obs = Observation(
        agent=Agent.THIEF,
        own_pos=(0, 4),
        opp_estimate=(4, 4),
        barriers=frozenset(),
        barriers_used=0,
        max_barriers=5,
        grid_size=(9, 9),
        move_count=5,
    )
    brief = build_tactical_brief(obs)
    assert "potential U" in brief
    assert "MUST MOVE" in brief


def test_tactical_brief_lists_ranked_hints() -> None:
    obs = Observation(
        agent=Agent.COP,
        own_pos=(1, 1),
        opp_estimate=(3, 3),
        barriers=frozenset(),
        barriers_used=1,
        max_barriers=5,
        grid_size=(5, 5),
        move_count=5,
    )
    brief = build_tactical_brief(obs)
    assert "Ranked action hints" in brief
    assert "Manhattan distance" in brief
