"""Tabular Q-learning baseline strategy.

The strategy uses compact, discretized observations so it remains lightweight
and deterministic enough for local orchestration tests.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from cop_thief.constants import COP_ACTIONS, MOVE_DELTAS, THIEF_ACTIONS, Action, Agent
from cop_thief.services.orchestrator._types import Observation
from cop_thief.services.strategy._barrier_policy import can_place_barrier
from cop_thief.services.strategy.base import Strategy, StrategyDecision

StateKey = tuple[str, int, int, int, int, int]


@dataclass
class _Transition:
    state: StateKey
    action: Action
    distance: int


def _distance(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _target(obs: Observation, action: Action) -> tuple[int, int]:
    dr, dc = MOVE_DELTAS[action]
    return (obs.own_pos[0] + dr, obs.own_pos[1] + dc)


def _legal_actions(obs: Observation) -> list[Action]:
    actions = COP_ACTIONS if obs.agent is Agent.COP else THIEF_ACTIONS
    legal: list[Action] = []
    rows, cols = obs.grid_size
    for action in actions:
        if action is Action.PLACE_BARRIER:
            if can_place_barrier(obs):
                legal.append(action)
            continue
        tgt = _target(obs, action)
        if 0 <= tgt[0] < rows and 0 <= tgt[1] < cols and tgt not in obs.barriers:
            legal.append(action)
    return legal or [Action.STAY]


def _state_key(obs: Observation) -> StateKey:
    dr = obs.opp_estimate[0] - obs.own_pos[0]
    dc = obs.opp_estimate[1] - obs.own_pos[1]
    return (
        obs.agent.value,
        max(-1, min(1, dr)),
        max(-1, min(1, dc)),
        min(obs.barriers_used, obs.max_barriers),
        obs.grid_size[0],
        obs.grid_size[1],
    )


@dataclass
class QLearningStrategy(Strategy):
    """Small epsilon-greedy tabular Q-learning policy."""

    learning_rate: float = 0.1
    discount_factor: float = 0.95
    epsilon: float = 0.1
    seed: int | None = None
    q_table: dict[StateKey, dict[Action, float]] = field(default_factory=dict)
    _previous: dict[Agent, _Transition] = field(default_factory=dict)
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialise deterministic RNG when a seed is supplied."""
        self._rng = random.Random(self.seed)

    async def decide(self, obs: Observation) -> StrategyDecision:
        """Choose an action and update the prior transition with shaped reward."""
        action = self.choose(obs)
        message = "Updating my search table." if obs.agent is Agent.COP else "Revaluing my escape."
        return StrategyDecision(action=action, nl_message=message)

    def choose(self, obs: Observation) -> Action:
        """Return an epsilon-greedy action for *obs*."""
        state = _state_key(obs)
        legal = _legal_actions(obs)
        self._ensure_state(state, legal)
        self._update_previous(obs, state, legal)
        if self._rng.random() < self.epsilon:
            action = self._rng.choice(legal)
        else:
            values = self.q_table[state]
            action = max(legal, key=lambda candidate: values[candidate])
        distance = _distance(obs.own_pos, obs.opp_estimate)
        self._previous[obs.agent] = _Transition(state, action, distance)
        return action

    def _ensure_state(self, state: StateKey, actions: list[Action]) -> None:
        values = self.q_table.setdefault(state, {})
        for action in actions:
            values.setdefault(action, 0.0)

    def _update_previous(self, obs: Observation, next_state: StateKey, legal: list[Action]) -> None:
        prev = self._previous.get(obs.agent)
        if prev is None:
            return
        current_distance = _distance(obs.own_pos, obs.opp_estimate)
        reward = prev.distance - current_distance
        if obs.agent is Agent.THIEF:
            reward = -reward
        old = self.q_table[prev.state][prev.action]
        best_next = max(self.q_table[next_state][action] for action in legal)
        td_target = reward + self.discount_factor * best_next
        self.q_table[prev.state][prev.action] = old + self.learning_rate * (td_target - old)
