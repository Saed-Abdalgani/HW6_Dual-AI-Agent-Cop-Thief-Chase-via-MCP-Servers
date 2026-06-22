"""Provider-agnostic LLM client with heuristic fallback.

Traces: FR-LLM1/2/4, ADR-6, T-P3-03, T-P3-05.
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable

from cop_thief.services.orchestrator._llm_http import call_llm_api, load_api_key
from cop_thief.services.orchestrator._llm_parse import parse_llm_json
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
        schema = json.dumps({"action": "<action>", "nl_message": "<text>"})
        return (
            f"You are the {obs.agent.value} in a {obs.grid_size[0]}x{obs.grid_size[1]} chase game. "
            f"Your position: {obs.own_pos}. Opponent estimate: {obs.opp_estimate}. "
            f"Moves so far: {obs.move_count}. Last message: {obs.last_message!r}. "
            "Your nl_message must be natural language with coarse hints only; "
            "do not include literal row/column coordinates. "
            f"Reply with JSON only matching: {schema}"
        )

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

    async def decide(self, obs: Observation) -> LlmDecision:
        """Return an action + NL message, falling back to heuristic if needed."""
        try:
            raw = await self._call_provider(self._build_prompt(obs))
            decision = parse_llm_json(raw)
            return decision
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
