"""Prompt-based strategy delegating to :class:`LlmClient`.

Traces: ADR-6, PLAN §13, T-P4-11.
"""

from __future__ import annotations

from cop_thief.services.orchestrator._types import Observation
from cop_thief.services.orchestrator.llm_client import LlmClient
from cop_thief.services.strategy.base import Strategy, StrategyDecision


class LlmStrategy(Strategy):
    """Return ``{action, nl_message}`` from the configured LLM provider."""

    def __init__(self, llm: LlmClient) -> None:
        """Store the shared LLM client."""
        self._llm = llm

    async def decide(self, obs: Observation) -> StrategyDecision:
        """Call the LLM and map to :class:`StrategyDecision`."""
        result = await self._llm.decide(obs)
        return StrategyDecision(action=result.action, nl_message=result.nl_message)
