"""Strategy factory keyed by config ``strategy`` value.

Traces: FR-D3, T-P4-02.
"""

from __future__ import annotations

from cop_thief.constants import Strategy as StrategyName
from cop_thief.services.orchestrator.llm_client import LlmClient
from cop_thief.services.strategy.base import Strategy
from cop_thief.services.strategy.heuristic import HeuristicStrategy
from cop_thief.services.strategy.llm_strategy import LlmStrategy
from cop_thief.shared.config import Config


def create_strategy(config: Config, llm: LlmClient | None = None) -> Strategy:
    """Return the strategy implementation for *config.strategy*.

    Args:
        config: Runtime configuration (``strategy`` key selects implementation).
        llm: Required when ``strategy`` is ``llm``.

    Raises:
        ValueError: When ``strategy`` is unknown or ``llm`` is missing for LLM mode.

    """
    name = config.strategy
    if name is StrategyName.HEURISTIC:
        return HeuristicStrategy()
    if name is StrategyName.LLM:
        if llm is None:
            msg = "LlmClient is required for strategy='llm'."
            raise ValueError(msg)
        return LlmStrategy(llm)
    if name is StrategyName.QLEARNING:
        msg = (
            f"Strategy '{name}' is not implemented yet. "
            "Use 'heuristic' or 'llm'."
        )
        raise ValueError(msg)
    msg = f"Unknown strategy '{name}'."
    raise ValueError(msg)
