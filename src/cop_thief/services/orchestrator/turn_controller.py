"""Per-turn orchestration: LLM decision → MCP message → apply action.

Traces: FR-O3, PLAN §11, T-P3-06, T-P3-07.
"""

from __future__ import annotations

from dataclasses import dataclass

from cop_thief.constants import Action, Agent, Strategy
from cop_thief.services.orchestrator._types import LlmDecision, Observation
from cop_thief.services.orchestrator.estimator import OpponentEstimator
from cop_thief.services.orchestrator.llm_client import LlmClient
from cop_thief.services.orchestrator.mcp_client import McpClient
from cop_thief.services.orchestrator.validator import ActionValidator
from cop_thief.services.strategy.heuristic import choose_heuristic_action
from cop_thief.shared.config import Config
from cop_thief.shared.logging import get_logger

_log = get_logger(__name__)


@dataclass
class TurnResult:
    """Outcome of a single orchestrated turn."""

    agent: Agent
    action: Action
    legal: bool
    nl_message: str


class TurnController:
    """Execute one turn: context → LLM → validate → MCP send → apply."""

    def __init__(
        self,
        config: Config,
        mcp: McpClient,
        llm: LlmClient,
        estimator: OpponentEstimator,
        validator: ActionValidator | None = None,
    ) -> None:
        """Wire dependencies for turn execution."""
        self._cfg = config
        self._mcp = mcp
        self._llm = llm
        self._estimator = estimator
        self._validator = validator or ActionValidator()

    async def _load_context(self, agent: Agent, move_count: int) -> Observation:
        pos_resp = await self._mcp.verify_position(agent.value)
        own_pos = tuple(pos_resp["pos"])
        msg_resp = await self._mcp.receive_message(agent.value)
        last_msg = msg_resp.get("text", "")
        self._estimator.update_from_message(last_msg)
        return self._estimator.build_observation(
            agent=agent,
            own_pos=own_pos,
            barriers=frozenset(),
            barriers_used=0,
            max_barriers=self._cfg.max_barriers,
            move_count=move_count,
            last_message=last_msg,
        )

    async def _decide(self, obs: Observation) -> LlmDecision:
        if self._cfg.strategy is Strategy.HEURISTIC:
            action = choose_heuristic_action(obs)
            msg = "Closing in." if obs.agent is Agent.COP else "Slipping away."
            return LlmDecision(action=action, nl_message=msg)
        return await self._llm.decide(obs)

    async def execute_turn(self, agent: Agent, move_count: int) -> TurnResult:
        """Run the full per-turn pipeline for *agent*."""
        obs = await self._load_context(agent, move_count)
        decision = await self._decide(obs)
        action = decision.action
        if not self._validator.is_legal(obs, action):
            _log.warning(
                "Action %s rejected for %s; heuristic fallback.",
                action, agent,
            )
            action = choose_heuristic_action(obs)
        await self._mcp.send_message(agent.value, decision.nl_message)
        apply_resp = await self._mcp.apply_action(agent.value, action.value)
        legal = bool(apply_resp.get("legal", False))
        if not legal:
            fallback = choose_heuristic_action(obs)
            apply_resp = await self._mcp.apply_action(agent.value, fallback.value)
            action = fallback
            legal = bool(apply_resp.get("legal", False))
        return TurnResult(agent=agent, action=action, legal=legal, nl_message=decision.nl_message)
