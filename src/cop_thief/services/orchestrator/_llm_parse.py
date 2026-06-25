"""Parse LLM JSON output into :class:`LlmDecision`.

Traces: ADR-6, PLAN §13, T-P3-04.
"""

from __future__ import annotations

import json
import re
from typing import Any

from cop_thief.constants import Action, Agent
from cop_thief.services.orchestrator._types import LlmDecision

_DIRECTION_ALIASES: dict[str, str] = {
    "north": "up",
    "south": "down",
    "east": "right",
    "west": "left",
    "n": "up",
    "s": "down",
    "e": "right",
    "w": "left",
    "northeast": "up_right",
    "north_east": "up_right",
    "northwest": "up_left",
    "north_west": "up_left",
    "southeast": "down_right",
    "south_east": "down_right",
    "southwest": "down_left",
    "south_west": "down_left",
    "move_north": "up",
    "move_south": "down",
    "move_east": "right",
    "move_west": "left",
    "move_northeast": "up_right",
    "move_northwest": "up_left",
    "move_southeast": "down_right",
    "move_southwest": "down_left",
}

_MISC_ALIASES: dict[str, str] = {
    "move": "stay",
    "go": "stay",
    "wait": "stay",
    "hold": "stay",
    "search": "stay",
    "block": "place_barrier",
    "barrier": "place_barrier",
    "place_barrier": "place_barrier",
    "place barrier": "place_barrier",
}


def _normalize_action_token(raw: str) -> str:
    """Map common LLM action strings to engine action names."""
    text = raw.strip().lower()
    text = re.sub(r"[\s\-]+", "_", text)
    text = re.sub(r"^move_", "", text)
    text = re.sub(r"^go_", "", text)
    if text in _DIRECTION_ALIASES:
        return _DIRECTION_ALIASES[text]
    if text in _MISC_ALIASES:
        return _MISC_ALIASES[text]
    spaced = text.replace("_", " ")
    if spaced in _MISC_ALIASES:
        return _MISC_ALIASES[spaced]
    if spaced in _DIRECTION_ALIASES:
        return _DIRECTION_ALIASES[spaced]
    return text.replace(" ", "_")


def resolve_llm_action(raw: str, agent: Agent | None = None) -> Action:
    """Resolve an LLM action string, including common aliases."""
    normalized = _normalize_action_token(raw)
    if agent is Agent.THIEF and normalized == "place_barrier":
        msg = f"Thief cannot use action '{raw}'."
        raise ValueError(msg)
    try:
        return Action(normalized)
    except ValueError as exc:
        msg = f"Unknown action '{raw}' in LLM output."
        raise ValueError(msg) from exc


def parse_llm_json(raw: str, agent: Agent | None = None) -> LlmDecision:
    """Parse *raw* LLM text into an :class:`LlmDecision`.

    Accepts a bare JSON object or one embedded in markdown fences.

    Raises:
        ValueError: When JSON is missing required keys or action is unknown.

    """
    text = raw.strip()
    fence = re.search(r"\{[\s\S]*\}", text)
    if fence:
        text = fence.group(0)
    data: dict[str, Any] = json.loads(text)
    action_str = data.get("action")
    nl_message = data.get("nl_message", "")
    if not action_str or not isinstance(nl_message, str):
        msg = "LLM output must contain 'action' and 'nl_message'."
        raise ValueError(msg)
    action = resolve_llm_action(str(action_str), agent=agent)
    return LlmDecision(action=action, nl_message=nl_message)
