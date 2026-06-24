"""Unit tests for strategy factory."""

from __future__ import annotations

import pytest

from cop_thief.constants import Strategy as StrategyName
from cop_thief.services.orchestrator.llm_client import LlmClient
from cop_thief.services.strategy.factory import create_strategy
from cop_thief.services.strategy.heuristic import HeuristicStrategy
from cop_thief.services.strategy.llm_strategy import LlmStrategy
from cop_thief.services.strategy.qlearning import QLearningStrategy
from cop_thief.shared._config_schemas import QLearningConfig
from cop_thief.shared.config import Config
from cop_thief.shared.gatekeeper import Gatekeeper


def test_factory_selects_heuristic(
    valid_config_yaml: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CONFIG_PATH", str(valid_config_yaml))
    cfg = Config.from_env()
    assert isinstance(create_strategy(cfg), HeuristicStrategy)


def test_factory_selects_llm(valid_config_yaml: object, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONFIG_PATH", str(valid_config_yaml))
    cfg = Config.from_env()
    cfg = cfg.model_copy(update={"strategy": StrategyName.LLM})
    llm = LlmClient(cfg, Gatekeeper(cfg.gatekeeper))
    assert isinstance(create_strategy(cfg, llm), LlmStrategy)


def test_factory_selects_qlearning(
    valid_config_yaml: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CONFIG_PATH", str(valid_config_yaml))
    cfg = Config.from_env().model_copy(
        update={
            "strategy": StrategyName.QLEARNING,
            "qlearning": QLearningConfig(learning_rate=0.25, epsilon=0.05),
        },
    )
    strategy = create_strategy(cfg)
    assert isinstance(strategy, QLearningStrategy)
    assert strategy.learning_rate == 0.25  # noqa: PLR2004
    assert strategy.epsilon == 0.05  # noqa: PLR2004


def test_factory_llm_requires_client(
    valid_config_yaml: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CONFIG_PATH", str(valid_config_yaml))
    cfg = Config.from_env().model_copy(update={"strategy": StrategyName.LLM})
    with pytest.raises(ValueError, match="LlmClient is required"):
        create_strategy(cfg)
