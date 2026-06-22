"""Parse LLM JSON output into :class:`LlmDecision`.

Traces: ADR-6, PLAN §13, T-P3-04.
"""

from __future__ import annotations

import json
import re
from typing import Any

from cop_thief.constants import Action
from cop_thief.services.orchestrator._types import LlmDecision


def parse_llm_json(raw: str) -> LlmDecision:
    """Parse *raw* LLM text into an :class:`LlmDecision`.

    Accepts a bare JSON object or one embedded in markdown fences.

    Raises:
        ValueError: When JSON is missing required keys or action is unknown.

    """
    text = raw.strip()
    fence = re.search(r"\{[\s\S]*\}", text)
    if fence:
        text = fence.group(0)
    data: dict[str, Any] = json.loads(text)
    action_str = data.get("action")
    nl_message = data.get("nl_message", "")
    if not action_str or not isinstance(nl_message, str):
        msg = "LLM output must contain 'action' and 'nl_message'."
        raise ValueError(msg)
    try:
        action = Action(action_str)
    except ValueError as exc:
        msg = f"Unknown action '{action_str}' in LLM output."
        raise ValueError(msg) from exc
    return LlmDecision(action=action, nl_message=nl_message)
