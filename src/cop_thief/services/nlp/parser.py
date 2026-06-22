"""Parse free-text messages into coarse opponent-location cues.

Traces: FR-NL2, FR-NL3, PLAN §14, T-P5-04, T-P5-06.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_DIRECTIONS = {
    "north": ("north", "up", "upper", "top"),
    "south": ("south", "down", "lower", "bottom"),
    "west": ("west", "left"),
    "east": ("east", "right"),
}
_REGIONS = {
    "northwest": ("northwest", "north-west", "upper left", "top left"),
    "northeast": ("northeast", "north-east", "upper right", "top right"),
    "southwest": ("southwest", "south-west", "lower left", "bottom left"),
    "southeast": ("southeast", "south-east", "lower right", "bottom right"),
    "center": ("center", "centre", "middle"),
    "north": ("north wall", "northern edge", "top edge"),
    "south": ("south wall", "southern edge", "bottom edge"),
    "west": ("west wall", "western edge", "left wall"),
    "east": ("east wall", "eastern edge", "right wall"),
}
_INTENTS = {
    "probe": ("where", "which wall", "show yourself", "are you"),
    "chase": ("closing", "chasing", "pressing", "net", "trap"),
    "evade": ("slipping", "hiding", "vanishing", "away", "escape"),
    "bluff": ("maybe", "perhaps", "believe me", "or maybe", "guess"),
}
_HEDGES = ("maybe", "perhaps", "guess", "might", "or maybe")


@dataclass(frozen=True)
class ParsedMessage:
    """Coarse interpretation of an opponent's natural-language message."""

    intent: str
    directions: frozenset[str]
    regions: frozenset[str]
    confidence: float
    ambiguous: bool


def _contains(text: str, phrase: str) -> bool:
    pattern = rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])"
    return re.search(pattern, text) is not None


def parse_message(text: str) -> ParsedMessage:
    """Extract intent plus coarse direction/region cues from free text."""
    lower = " ".join((text or "").lower().split())
    if not lower:
        return ParsedMessage("unknown", frozenset(), frozenset(), 0.0, True)

    directions = {
        name for name, words in _DIRECTIONS.items() if any(_contains(lower, w) for w in words)
    }
    regions = {
        name for name, words in _REGIONS.items() if any(_contains(lower, w) for w in words)
    }
    intents = [name for name, words in _INTENTS.items() if any(_contains(lower, w) for w in words)]
    intent = intents[0] if intents else "unknown"
    confidence = min(1.0, 0.2 + 0.2 * len(directions) + 0.15 * len(regions))
    if intent != "unknown":
        confidence += 0.15
    if any(_contains(lower, hedge) for hedge in _HEDGES):
        confidence = max(0.1, confidence - 0.25)
    ambiguous = confidence < 0.35 or (not directions and not regions)
    return ParsedMessage(intent, frozenset(directions), frozenset(regions), confidence, ambiguous)


def cue_target(
    parsed: ParsedMessage,
    grid_size: tuple[int, int],
    current: tuple[int, int],
) -> tuple[int, int]:
    """Translate parsed cues into a coarse target cell within the board."""
    if parsed.ambiguous:
        return current
    rows, cols = grid_size
    r, c = current
    region = next(iter(parsed.regions), "")
    if region:
        r, c = _region_anchor(region, rows, cols, r, c)
    for direction in parsed.directions:
        if direction == "north":
            r = max(0, r - 1)
        elif direction == "south":
            r = min(rows - 1, r + 1)
        elif direction == "west":
            c = max(0, c - 1)
        elif direction == "east":
            c = min(cols - 1, c + 1)
    return (r, c)


def _region_anchor(region: str, rows: int, cols: int, r: int, c: int) -> tuple[int, int]:
    anchors = {
        "northwest": (0, 0),
        "northeast": (0, cols - 1),
        "southwest": (rows - 1, 0),
        "southeast": (rows - 1, cols - 1),
        "center": (rows // 2, cols // 2),
        "north": (0, c),
        "south": (rows - 1, c),
        "west": (r, 0),
        "east": (r, cols - 1),
    }
    return anchors.get(region, (r, c))
