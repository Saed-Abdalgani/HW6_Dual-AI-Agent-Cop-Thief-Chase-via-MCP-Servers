"""Unit tests for thief APF scoring."""

from __future__ import annotations

from cop_thief.constants import Action, Agent
from cop_thief.services.orchestrator._llm_tactics import rank_actions
from cop_thief.services.orchestrator._thief_apf import thief_apf_score
from cop_thief.services.orchestrator._types import Observation


def test_thief_must_move_when_legal_moves_exist() -> None:
    obs = Observation(
        agent=Agent.THIEF,
        own_pos=(2, 2),
        opp_estimate=(2, 3),
        barriers=frozenset(),
        barriers_used=0,
        max_barriers=5,
        grid_size=(5, 5),
        move_count=10,
    )
    stay_score, stay_reason = thief_apf_score(obs, Action.STAY)
    top = rank_actions(obs, top_n=1)[0]
    assert stay_score < -100
    assert "must move" in stay_reason
    assert top.action is not Action.STAY


def test_thief_apf_prefers_interior_over_edge_on_9x9() -> None:
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
    assert top.action is not Action.STAY
    assert "minimize U" in top.reason or "maximin" in top.reason


def test_choose_thief_action_flees_adjacent_cop() -> None:
    from cop_thief.services.orchestrator._thief_apf import choose_thief_action, chebyshev

    obs = Observation(
        agent=Agent.THIEF,
        own_pos=(4, 4),
        opp_estimate=(4, 5),
        barriers=frozenset(),
        barriers_used=0,
        max_barriers=5,
        grid_size=(9, 9),
        move_count=5,
    )
    action = choose_thief_action(obs)
    assert action is not Action.STAY
    dr, dc = {
        Action.UP: (-1, 0),
        Action.DOWN: (1, 0),
        Action.LEFT: (0, -1),
        Action.RIGHT: (0, 1),
        Action.UP_LEFT: (-1, -1),
        Action.UP_RIGHT: (-1, 1),
        Action.DOWN_LEFT: (1, -1),
        Action.DOWN_RIGHT: (1, 1),
    }[action]
    nxt = (obs.own_pos[0] + dr, obs.own_pos[1] + dc)
    assert chebyshev(nxt, obs.opp_estimate) >= chebyshev(obs.own_pos, obs.opp_estimate)


def test_thief_stay_scores_best_when_surrounded() -> None:
    barriers = frozenset({(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)})
    obs = Observation(
        agent=Agent.THIEF,
        own_pos=(0, 0),
        opp_estimate=(4, 4),
        barriers=barriers,
        barriers_used=2,
        max_barriers=5,
        grid_size=(5, 5),
        move_count=5,
    )
    top = rank_actions(obs, top_n=1)[0]
    assert top.action is Action.STAY
