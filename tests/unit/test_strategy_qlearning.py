"""Unit tests for tabular Q-learning strategy."""

from __future__ import annotations

from cop_thief.constants import Action, Agent
from cop_thief.services.orchestrator._types import Observation
from cop_thief.services.strategy.qlearning import QLearningStrategy


def _obs(
    agent: Agent,
    own: tuple[int, int],
    opp: tuple[int, int],
    *,
    barriers: frozenset[tuple[int, int]] = frozenset(),
) -> Observation:
    return Observation(
        agent=agent,
        own_pos=own,
        opp_estimate=opp,
        barriers=barriers,
        barriers_used=0,
        max_barriers=5,
        grid_size=(5, 5),
        move_count=0,
    )


def test_qlearning_returns_legal_action() -> None:
    strategy = QLearningStrategy(epsilon=0.0, seed=1)

    action = strategy.choose(_obs(Agent.THIEF, (0, 0), (4, 4)))

    assert action in {
        Action.DOWN,
        Action.RIGHT,
        Action.DOWN_RIGHT,
        Action.STAY,
    }


def test_qlearning_updates_table_after_next_observation() -> None:
    strategy = QLearningStrategy(epsilon=0.0, seed=1)
    first = _obs(Agent.COP, (4, 4), (0, 0))
    strategy.choose(first)

    strategy.choose(_obs(Agent.COP, (3, 3), (0, 0)))

    assert any(value != 0.0 for row in strategy.q_table.values() for value in row.values())


def test_qlearning_does_not_choose_duplicate_barrier() -> None:
    strategy = QLearningStrategy(epsilon=0.0, seed=1)

    action = strategy.choose(_obs(Agent.COP, (1, 0), (0, 0), barriers=frozenset({(1, 0)})))

    assert action is not Action.PLACE_BARRIER
