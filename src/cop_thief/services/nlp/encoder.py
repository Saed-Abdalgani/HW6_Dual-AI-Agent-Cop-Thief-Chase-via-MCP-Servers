"""Generate coordinate-free natural-language turn messages.

Traces: FR-NL1, FR-NL4, T-P5-02, T-P5-03.
"""

from __future__ import annotations

import re

from cop_thief.constants import Action, Agent
from cop_thief.services.orchestrator._types import Observation

_COORD_RE = re.compile(r"[\[(]?\s*\d+\s*[,/]\s*\d+\s*[\])]?")
_GENERIC = {"closing in.", "slipping away.", "moving on instinct.", "i'll wait here."}
_ACTION_DIR = {
    Action.UP: "north",
    Action.DOWN: "south",
    Action.LEFT: "west",
    Action.RIGHT: "east",
    Action.UP_LEFT: "northwest",
    Action.UP_RIGHT: "northeast",
    Action.DOWN_LEFT: "southwest",
    Action.DOWN_RIGHT: "southeast",
    Action.STAY: "still",
    Action.PLACE_BARRIER: "a blocked path",
}


def contains_raw_coordinate(text: str) -> bool:
    """Return True when text appears to expose literal grid coordinates."""
    return _COORD_RE.search(text or "") is not None


def sanitize_message(text: str) -> str:
    """Remove coordinate-like fragments from a strategy/LLM message."""
    return " ".join(_COORD_RE.sub("nearby", text or "").split()).strip()


def describe_position(pos: tuple[int, int], grid_size: tuple[int, int]) -> str:
    """Return a coordinate-free region description for a grid position."""
    return _region_phrase(pos, grid_size)


def encode_message(
    obs: Observation,
    action: Action,
    proposed: str = "",
    *,
    tone: str = "balanced",
) -> str:
    """Return free-text that hints at intent without sending raw coordinates."""
    cleaned = sanitize_message(proposed)
    if cleaned and cleaned.lower() not in _GENERIC:
        return cleaned[:240]
    direction = _ACTION_DIR[action]
    region = _region_phrase(obs.own_pos, obs.grid_size)
    if tone == "deceptive" or (obs.agent is Agent.THIEF and tone != "probing"):
        return _deceptive_message(obs.agent, direction, region)
    if tone == "probing" or obs.agent is Agent.COP:
        return _probing_message(direction, region)
    return f"I am drifting through the {region}, watching the {direction} lane."


def _region_phrase(pos: tuple[int, int], grid_size: tuple[int, int]) -> str:
    rows, cols = grid_size
    row, col = pos
    vertical = "northern" if row < rows / 3 else "southern" if row >= rows * 2 / 3 else "central"
    horizontal = "western" if col < cols / 3 else "eastern" if col >= cols * 2 / 3 else "middle"
    if vertical == "central" and horizontal == "middle":
        return "center lanes"
    return f"{vertical} {horizontal} lanes"


def _probing_message(direction: str, region: str) -> str:
    if direction == "a blocked path":
        return "I am closing a route and listening for which wall you favor."
    if direction == "still":
        return f"I am holding in the {region} and testing your patience."
    return f"I am pressing toward the {direction} side from the {region}."


def _deceptive_message(agent: Agent, direction: str, region: str) -> str:
    if direction == "still":
        return f"I might be quiet in the {region}, unless that silence is bait."
    role = "You may think I am" if agent is Agent.THIEF else "I want you watching me"
    return f"{role} leaning {direction} near the {region}; trust that only halfway."
