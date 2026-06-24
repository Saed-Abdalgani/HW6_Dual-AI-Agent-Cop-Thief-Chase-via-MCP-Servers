"""Shared datatypes for the orchestrator layer.

Traces: PLAN §4, §10.3, T-P3-04.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cop_thief.constants import Action, Agent


@dataclass(frozen=True)
class LlmDecision:
    """Parsed LLM output contract ``{action, nl_message}``."""

    action: Action
    nl_message: str


@dataclass(frozen=True)
class Observation:
    """Partial observation passed to strategy / LLM on each turn."""

    agent: Agent
    own_pos: tuple[int, int]
    opp_estimate: tuple[int, int]
    barriers: frozenset[tuple[int, int]]
    barriers_used: int
    max_barriers: int
    grid_size: tuple[int, int]
    move_count: int
    last_message: str = ""


@dataclass
class HealthStatus:
    """Reachability snapshot for SDK ``health_check()``."""

    cop_mcp: bool = False
    thief_mcp: bool = False
    llm: bool = False

    @property
    def all_ok(self) -> bool:
        """Return True when every dependency is reachable."""
        return self.cop_mcp and self.thief_mcp and self.llm


@dataclass
class GameState:
    """Current game snapshot for GUI rendering."""

    cop_pos: tuple[int, int] = (0, 0)
    thief_pos: tuple[int, int] = (0, 0)
    barriers: list[tuple[int, int]] = field(default_factory=list)
    move_count: int = 0
    barriers_used: int = 0
    max_barriers: int = 5
    over: bool = False
    winner: str | None = None
    scores: dict[str, int] = field(default_factory=lambda: {"cop": 0, "thief": 0})
    sub_game_index: int = 0
    latest_message: str = ""
    grid_size: tuple[int, int] = (5, 5)
    idle: bool = False
