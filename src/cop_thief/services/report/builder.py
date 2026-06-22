"""Build and validate the final JSON report.

Traces: FR-E4, FR-E5, T-P8-01..04.
"""

from __future__ import annotations

import json
from typing import Any

from cop_thief.services.engine._lifecycle_types import FullGameResult, SubGameResult
from cop_thief.shared.config import Config

REPORT_KEYS = {
    "group_name",
    "students",
    "github_repo",
    "cop_mcp_url",
    "thief_mcp_url",
    "timezone",
    "sub_games",
    "totals",
}


def build_report(config: Config, result: FullGameResult) -> dict[str, Any]:
    """Return the final report dict using the PRD section 12 contract."""
    return {
        "group_name": config.report.group_name,
        "students": list(config.report.students),
        "github_repo": config.report.github_repo,
        "cop_mcp_url": config.mcp.cop_url,
        "thief_mcp_url": config.mcp.thief_url,
        "timezone": config.timezone,
        "sub_games": [_sub_game_dict(sub_game) for sub_game in result.sub_games],
        "totals": {"cop": result.totals.cop, "thief": result.totals.thief},
    }


def report_to_json(config: Config, result: FullGameResult) -> str:
    """Serialize a final report to strict JSON only."""
    body = json.dumps(build_report(config, result), ensure_ascii=True, sort_keys=True)
    validate_report_json(body)
    return body


def validate_report_json(body: str) -> dict[str, Any]:
    """Validate that *body* is JSON and matches the top-level contract."""
    data = json.loads(body)
    if not isinstance(data, dict) or set(data) != REPORT_KEYS:
        msg = "Report JSON top-level keys do not match the PRD contract."
        raise ValueError(msg)
    if not isinstance(data["sub_games"], list):
        msg = "Report JSON sub_games must be a list."
        raise ValueError(msg)
    totals = data["totals"]
    if not isinstance(totals, dict) or set(totals) != {"cop", "thief"}:
        msg = "Report JSON totals must contain cop and thief."
        raise ValueError(msg)
    return data


def _sub_game_dict(result: SubGameResult) -> dict[str, Any]:
    return {
        "index": result.index,
        "winner": result.winner.value,
        "moves": result.moves_used,
        "barriers_used": result.barriers_used,
        "scores": {"cop": result.score.cop, "thief": result.score.thief},
    }
