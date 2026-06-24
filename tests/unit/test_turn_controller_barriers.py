"""TurnController barrier-observation tests."""

from __future__ import annotations

from cop_thief.constants import Action, Agent
from cop_thief.services.orchestrator.estimator import OpponentEstimator
from cop_thief.services.orchestrator.turn_controller import TurnController
from cop_thief.services.strategy.base import Strategy, StrategyDecision
from cop_thief.shared.config import Config


class _CaptureStrategy(Strategy):
    def __init__(self) -> None:
        self.observation = None

    async def decide(self, obs):  # noqa: ANN001, ANN201
        self.observation = obs
        return StrategyDecision(action=Action.STAY, nl_message="waiting")


class _McpStub:
    async def game_status(self) -> dict:
        return {"barriers": [[1, 1], [3, 3]], "barriers_used": 2}

    async def verify_position(self, agent: str) -> dict:  # noqa: ARG002
        return {"pos": [2, 2]}

    async def receive_message(self, agent: str) -> dict:  # noqa: ARG002
        return {"text": ""}

    async def send_message(self, from_agent: str, text: str) -> dict:  # noqa: ARG002
        return {"ok": True}

    async def apply_action(self, agent: str, action: str) -> dict:  # noqa: ARG002
        return {"legal": True, "state_delta": {"new_pos": [2, 2]}}


async def test_turn_controller_passes_game_status_barriers_to_strategy(
    valid_config_yaml,
) -> None:
    cfg = Config.from_yaml(valid_config_yaml)
    strategy = _CaptureStrategy()
    controller = TurnController(
        cfg,
        _McpStub(),  # type: ignore[arg-type]
        strategy,
        OpponentEstimator(cfg.grid_size),
    )

    await controller.execute_turn(Agent.COP, move_count=4)

    assert strategy.observation is not None
    assert strategy.observation.barriers == frozenset({(1, 1), (3, 3)})
    assert strategy.observation.barriers_used == 2
