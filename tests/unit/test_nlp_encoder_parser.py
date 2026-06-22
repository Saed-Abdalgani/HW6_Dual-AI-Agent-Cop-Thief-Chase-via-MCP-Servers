"""Unit tests for Phase P5 natural-language encoding and parsing."""

from __future__ import annotations

from cop_thief.constants import Action, Agent
from cop_thief.services.nlp.encoder import contains_raw_coordinate, encode_message
from cop_thief.services.nlp.parser import cue_target, parse_message
from cop_thief.services.orchestrator._types import Observation


def _obs(agent: Agent = Agent.THIEF) -> Observation:
    return Observation(
        agent=agent,
        own_pos=(2, 3),
        opp_estimate=(0, 0),
        barriers=frozenset(),
        barriers_used=0,
        max_barriers=5,
        grid_size=(5, 5),
        move_count=4,
    )


def test_encoder_removes_raw_coordinates() -> None:
    msg = encode_message(_obs(), Action.LEFT, "I am at (2, 3), come here.")
    assert contains_raw_coordinate(msg) is False
    assert "nearby" in msg


def test_encoder_generates_free_text_for_generic_strategy_message() -> None:
    msg = encode_message(_obs(Agent.COP), Action.UP_RIGHT, "Closing in.", tone="probing")
    assert "northeast" in msg
    assert contains_raw_coordinate(msg) is False


def test_parser_extracts_direction_region_and_intent() -> None:
    parsed = parse_message("I am slipping along the eastern edge, maybe north.")
    assert "east" in parsed.regions
    assert "north" in parsed.directions
    assert parsed.intent == "evade"
    assert parsed.confidence > 0


def test_parser_marks_empty_message_ambiguous() -> None:
    parsed = parse_message("")
    assert parsed.ambiguous is True
    assert parsed.confidence == 0


def test_cue_target_moves_toward_coarse_hint() -> None:
    parsed = parse_message("I am near the north wall and moving east.")
    assert cue_target(parsed, (5, 5), (2, 2)) == (0, 3)
