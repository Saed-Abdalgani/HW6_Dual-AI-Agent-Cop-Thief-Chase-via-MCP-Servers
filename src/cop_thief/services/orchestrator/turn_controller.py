"""Per-turn orchestration: strategy decision → MCP message → apply action.

Traces: FR-O3, PLAN §11, T-P3-06, T-P4-01.
"""

from __future__ import annotations

from dataclasses import dataclass

from cop_thief.constants import Action, Agent
from cop_thief.services.nlp.encoder import encode_message
from cop_thief.services.nlp.transcript import TranscriptLogger
from cop_thief.services.orchestrator._types import Observation
from cop_thief.services.orchestrator.estimator import OpponentEstimator
from cop_thief.services.orchestrator.mcp_client import McpClient
from cop_thief.services.orchestrator.validator import ActionValidator
from cop_thief.services.strategy.base import Strategy
from cop_thief.services.strategy.heuristic import HeuristicStrategy, choose_heuristic_action
from cop_thief.shared.config import Config
from cop_thief.shared.logging import get_logger

_log = get_logger(__name__)
_FALLBACK = HeuristicStrategy()


@dataclass
class TurnResult:
    """Outcome of a single orchestrated turn."""

    agent: Agent
    action: Action
    legal: bool
    nl_message: str
    new_pos: tuple[int, int] | None = None
    barrier_placed: bool = False
    over: bool = False
    winner: str | None = None


class TurnController:
    """Execute one turn: context → strategy → validate → MCP send → apply."""

    def __init__(
        self,
        config: Config,
        mcp: McpClient,
        strategy: Strategy,
        estimator: OpponentEstimator,
        validator: ActionValidator | None = None,
        transcript: TranscriptLogger | None = None,
    ) -> None:
        """Wire dependencies for turn execution."""
        self._cfg = config
        self._mcp = mcp
        self._strategy = strategy
        self._estimator = estimator
        self._validator = validator or ActionValidator()
        self._transcript = transcript

    def start_transcript(self, sub_game_index: int) -> None:
        """Start a fresh NL transcript for a sub-game."""
        if self._transcript:
            self._transcript.start(sub_game_index)

    async def _load_context(self, agent: Agent, move_count: int) -> Observation:
        pos_resp = await self._mcp.verify_position(agent.value)
        own_pos = tuple(pos_resp["pos"])
        msg_resp = await self._mcp.receive_message(agent.value)
        last_msg = msg_resp.get("text", "")
        self._estimator.update_from_message(last_msg, agent)
        return self._estimator.build_observation(
            agent=agent,
            own_pos=own_pos,
            barriers=frozenset(),
            barriers_used=0,
            max_barriers=self._cfg.max_barriers,
            move_count=move_count,
            last_message=last_msg,
        )

    async def execute_turn(self, agent: Agent, move_count: int) -> TurnResult:
        """Run the full per-turn pipeline for *agent*."""
        obs = await self._load_context(agent, move_count)
        decision = await self._strategy.decide(obs)
        action = decision.action
        if not self._validator.is_legal(obs, action):
            _log.warning("Action %s rejected for %s; heuristic fallback.", action, agent)
            action = _FALLBACK.choose(obs)
        nl_message = encode_message(
            obs,
            action,
            decision.nl_message,
            tone=self._cfg.nlp.tone,
        )
        await self._mcp.send_message(agent.value, nl_message)
        apply_resp = await self._mcp.apply_action(agent.value, action.value)
        legal = bool(apply_resp.get("legal", False))
        if not legal:
            fallback = choose_heuristic_action(obs)
            apply_resp = await self._mcp.apply_action(agent.value, fallback.value)
            action = fallback
            legal = bool(apply_resp.get("legal", False))
        delta = apply_resp.get("state_delta", {})
        new_pos = tuple(delta["new_pos"]) if delta.get("new_pos") else None
        if legal:
            self._estimator.update_from_action(agent, action, new_pos)
        if self._transcript:
            self._transcript.record(agent, action, nl_message, move_count)
        return TurnResult(
            agent=agent,
            action=action,
            legal=legal,
            nl_message=nl_message,
            new_pos=new_pos,
            barrier_placed=bool(delta.get("barrier_placed", False)),
            over=bool(delta.get("over", False)),
            winner=delta.get("winner"),
        )
