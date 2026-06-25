"""Provider-agnostic LLM client with heuristic fallback.

Traces: FR-LLM1/2/4, ADR-6, T-P3-03, T-P3-05.
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable

from cop_thief.constants import Action, Agent
from cop_thief.services.nlp.encoder import sanitize_message
from cop_thief.services.orchestrator._llm_http import call_llm_api, load_api_key
from cop_thief.services.orchestrator._llm_parse import parse_llm_json
from cop_thief.services.orchestrator._llm_prompt import build_llm_prompt
from cop_thief.services.orchestrator._llm_tactics import rank_actions, score_action
from cop_thief.services.orchestrator._thief_apf import choose_thief_action
from cop_thief.services.orchestrator._types import LlmDecision, Observation
from cop_thief.services.strategy.heuristic import choose_heuristic_action
from cop_thief.shared._gatekeeper_types import OutboundRequest
from cop_thief.shared.config import Config
from cop_thief.shared.gatekeeper import Gatekeeper
from cop_thief.shared.logging import get_logger

_log = get_logger(__name__)

LlmCaller = Callable[[str], Awaitable[str]]


class LlmClient:
    """Call LLM via Gatekeeper; fall back to heuristic on failure."""

    def __init__(
        self,
        config: Config,
        gatekeeper: Gatekeeper,
        llm_caller: LlmCaller | None = None,
    ) -> None:
        """Wire config, gatekeeper, and optional injectable caller (tests)."""
        self._cfg = config
        self._gk = gatekeeper
        self._caller = llm_caller

    def _build_prompt(self, obs: Observation) -> str:
        return build_llm_prompt(obs)

    def _build_thief_taunt_prompt(self, obs: Observation, action: Action) -> str:
        schema = json.dumps({"action": action.value, "nl_message": "short taunt"})
        return (
            f"You are the thief on a {obs.grid_size[0]}x{obs.grid_size[1]} grid.\n"
            f"Your engine already chose action: {action.value}.\n"
            "Reply JSON only with the same action and a one-line coarse regional taunt "
            f"(no coordinates): {schema}"
        )

    def _guard_action(self, obs: Observation, decision: LlmDecision) -> LlmDecision:
        """Override weak cop LLM choices when tactical analysis strongly disagrees."""
        if obs.agent is Agent.THIEF:
            return decision
        hints = rank_actions(obs, top_n=12)
        if not hints:
            return decision
        best = hints[0]
        if best.action is decision.action:
            return decision
        chosen_score = score_action(obs, decision.action)
        if decision.action is Action.STAY and best.score >= 30:
            return LlmDecision(action=best.action, nl_message=decision.nl_message)
        if best.score >= 50 and best.score - chosen_score >= 45:
            return LlmDecision(action=best.action, nl_message=decision.nl_message)
        return decision

    async def _call_provider(self, prompt: str) -> str:
        api_key = load_api_key()
        if not api_key and not self._caller:
            msg = "LLM_API_KEY not set."
            raise ValueError(msg)

        async def _fn() -> str:
            if self._caller:
                return await self._caller(prompt)
            return await call_llm_api(self._cfg.llm, api_key, prompt)

        resp = await self._gk.call(
            OutboundRequest(target="llm", fn=_fn, metadata={"provider": self._cfg.llm.provider}),
        )
        return resp.result

    async def _thief_decide(self, obs: Observation) -> LlmDecision:
        """Thief movement from minimax APF engine; LLM only for NL taunt."""
        action = choose_thief_action(obs)
        nl_message = "Still moving."
        try:
            raw = await self._call_provider(self._build_thief_taunt_prompt(obs, action))
            parsed = parse_llm_json(raw, agent=Agent.THIEF)
            nl_message = parsed.nl_message
        except Exception as exc:  # noqa: BLE001
            _log.debug("Thief taunt LLM failed (%r); using default message.", exc)
        return LlmDecision(action=action, nl_message=sanitize_message(nl_message))

    async def decide(self, obs: Observation) -> LlmDecision:
        """Return an action + NL message, falling back to heuristic if needed."""
        if obs.agent is Agent.THIEF:
            return await self._thief_decide(obs)
        try:
            raw = await self._call_provider(self._build_prompt(obs))
            decision = parse_llm_json(raw, agent=obs.agent)
            decision = self._guard_action(obs, decision)
            return LlmDecision(
                action=decision.action,
                nl_message=sanitize_message(decision.nl_message),
            )
        except Exception as exc:  # noqa: BLE001
            _log.warning("LLM decision failed (%r); using heuristic fallback.", exc)
            action = choose_heuristic_action(obs)
            return LlmDecision(action=action, nl_message="Moving on instinct.")

    async def health_check(self) -> bool:
        """Return True when the LLM endpoint is reachable."""
        try:
            await self._call_provider('Respond with JSON: {"action":"stay","nl_message":"ok"}')
            return True
        except Exception:  # noqa: BLE001
            return False
