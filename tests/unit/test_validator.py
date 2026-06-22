"""Unit tests for client-side ActionValidator."""

from __future__ import annotations

from cop_thief.constants import Action, Agent
from cop_thief.services.orchestrator._types import Observation
from cop_thief.services.orchestrator.validator import ActionValidator


def _obs(agent: Agent = Agent.COP, pos: tuple[int, int] = (2, 2)) -> Observation:
    return Observation(
        agent=agent,
        own_pos=pos,
        opp_estimate=(0, 0),
        barriers=frozenset({(1, 2)}),
        barriers_used=0,
        max_barriers=5,
        grid_size=(5, 5),
        move_count=0,
    )


def test_validator_rejects_off_board() -> None:
    v = ActionValidator()
    assert v.is_legal(_obs(pos=(0, 0)), Action.UP) is False


def test_validator_rejects_blocked_cell() -> None:
    v = ActionValidator()
    assert v.is_legal(_obs(pos=(1, 1)), Action.RIGHT) is False


def test_validator_rejects_thief_barrier() -> None:
    v = ActionValidator()
    obs = _obs(agent=Agent.THIEF)
    assert v.is_legal(obs, Action.PLACE_BARRIER) is False


def test_validator_accepts_legal_move() -> None:
    v = ActionValidator()
    assert v.is_legal(_obs(), Action.DOWN) is True


def test_validator_barrier_budget() -> None:
    v = ActionValidator()
    obs = _obs()
    obs2 = Observation(
        agent=obs.agent,
        own_pos=obs.own_pos,
        opp_estimate=obs.opp_estimate,
        barriers=obs.barriers,
        barriers_used=5,
        max_barriers=5,
        grid_size=obs.grid_size,
        move_count=0,
    )
    assert v.is_legal(obs2, Action.PLACE_BARRIER) is False
