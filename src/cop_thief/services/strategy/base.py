"""Strategy interface for agent decision-making.

Traces: FR-D3, ADR-5, PLAN §14, T-P4-01.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from cop_thief.constants import Action
from cop_thief.services.orchestrator._types import Observation


@dataclass(frozen=True)
class StrategyDecision:
    """Action plus optional natural-language message for the opponent."""

    action: Action
    nl_message: str = ""


class Strategy(ABC):
    """Pluggable decision strategy selected via config."""

    @abstractmethod
    async def decide(self, obs: Observation) -> StrategyDecision:
        """Choose an action (and optional NL message) for *obs*."""

    def choose(self, obs: Observation) -> Action:
        """Return an action synchronously (heuristic/fallback strategies only)."""
        raise NotImplementedError(f"{type(self).__name__} does not support sync choose().")
