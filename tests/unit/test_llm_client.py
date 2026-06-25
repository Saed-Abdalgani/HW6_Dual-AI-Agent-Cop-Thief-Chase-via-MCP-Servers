"""Unit tests for LLM JSON parsing and heuristic fallback."""

from __future__ import annotations

import json

import pytest

from cop_thief.constants import Action, Agent
from cop_thief.services.nlp.encoder import contains_raw_coordinate
from cop_thief.services.orchestrator._llm_parse import parse_llm_json
from cop_thief.services.orchestrator._types import Observation
from cop_thief.services.orchestrator.llm_client import LlmClient
from cop_thief.shared.config import Config
from cop_thief.shared.gatekeeper import Gatekeeper


def test_parse_llm_json_valid() -> None:
    raw = json.dumps({"action": "up", "nl_message": "Heading north!"})
    decision = parse_llm_json(raw)
    assert decision.action is Action.UP
    assert decision.nl_message == "Heading north!"


def test_parse_llm_json_markdown_fence() -> None:
    raw = '```json\n{"action": "stay", "nl_message": "holding"}\n```'
    decision = parse_llm_json(raw)
    assert decision.action is Action.STAY


def test_parse_llm_json_invalid_action() -> None:
    with pytest.raises(ValueError, match="Unknown action"):
        parse_llm_json('{"action": "fly", "nl_message": "nope"}')


def test_parse_llm_json_aliases() -> None:
    assert parse_llm_json('{"action": "move east", "nl_message": "go"}').action is Action.RIGHT
    assert parse_llm_json('{"action": "block", "nl_message": "trap"}').action is Action.PLACE_BARRIER
    assert parse_llm_json('{"action": "search", "nl_message": "hmm"}').action is Action.STAY


def test_parse_llm_json_rejects_thief_barrier() -> None:
    with pytest.raises(ValueError, match="Thief cannot"):
        parse_llm_json('{"action": "block", "nl_message": "nope"}', agent=Agent.THIEF)


@pytest.mark.asyncio
async def test_llm_fallback_on_bad_json(
    valid_config_yaml: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CONFIG_PATH", str(valid_config_yaml))
    cfg = Config.from_env()

    async def bad_caller(prompt: str) -> str:  # noqa: ARG001
        return "not json at all"

    client = LlmClient(cfg, Gatekeeper(cfg.gatekeeper), llm_caller=bad_caller)
    obs = Observation(
        agent=Agent.THIEF,
        own_pos=(2, 2),
        opp_estimate=(0, 0),
        barriers=frozenset(),
        barriers_used=0,
        max_barriers=5,
        grid_size=(5, 5),
        move_count=0,
    )
    decision = await client.decide(obs)
    assert decision.action in Action
    assert decision.nl_message


@pytest.mark.asyncio
async def test_llm_guard_overrides_idle_stay(
    valid_config_yaml: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CONFIG_PATH", str(valid_config_yaml))
    cfg = Config.from_env()

    async def caller(prompt: str) -> str:  # noqa: ARG001
        return json.dumps({"action": "stay", "nl_message": "thinking..."})

    client = LlmClient(cfg, Gatekeeper(cfg.gatekeeper), llm_caller=caller)
    obs = Observation(
        agent=Agent.COP,
        own_pos=(2, 2),
        opp_estimate=(0, 0),
        barriers=frozenset(),
        barriers_used=0,
        max_barriers=5,
        grid_size=(5, 5),
        move_count=0,
    )
    decision = await client.decide(obs)
    assert decision.action is not Action.STAY


@pytest.mark.asyncio
async def test_llm_thief_uses_engine_not_llm_action(
    valid_config_yaml: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CONFIG_PATH", str(valid_config_yaml))
    cfg = Config.from_env()
    from cop_thief.services.orchestrator._thief_apf import choose_thief_action

    async def caller(prompt: str) -> str:  # noqa: ARG001
        return json.dumps({"action": "stay", "nl_message": "nope"})

    client = LlmClient(cfg, Gatekeeper(cfg.gatekeeper), llm_caller=caller)
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
    expected = choose_thief_action(obs)
    decision = await client.decide(obs)
    assert decision.action is expected
    assert decision.action is not Action.STAY


@pytest.mark.asyncio
async def test_llm_prompt_and_output_are_coordinate_free(
    valid_config_yaml: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CONFIG_PATH", str(valid_config_yaml))
    cfg = Config.from_env()
    prompts: list[str] = []

    async def caller(prompt: str) -> str:
        prompts.append(prompt)
        return json.dumps({"action": "stay", "nl_message": "I am at (2, 3)."})

    client = LlmClient(cfg, Gatekeeper(cfg.gatekeeper), llm_caller=caller)
    obs = Observation(
        agent=Agent.COP,
        own_pos=(2, 3),
        opp_estimate=(0, 0),
        barriers=frozenset(),
        barriers_used=2,
        max_barriers=5,
        grid_size=(5, 5),
        move_count=4,
    )
    decision = await client.decide(obs)

    assert prompts
    assert "place_barrier" in prompts[0]
    assert "Ranked action hints" in prompts[0]
    assert "Cop doctrine" in prompts[0]
    assert "(2, 3)" not in prompts[0]
    assert "2/5" not in prompts[0]
    assert contains_raw_coordinate(decision.nl_message) is False
