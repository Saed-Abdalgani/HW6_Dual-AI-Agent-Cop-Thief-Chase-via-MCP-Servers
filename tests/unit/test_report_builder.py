"""Unit tests for final JSON report builder."""

from __future__ import annotations

import json

import pytest

from cop_thief.constants import Outcome
from cop_thief.services.engine._lifecycle_types import FullGameResult, SubGameResult
from cop_thief.services.engine.scoring import SubGameScore
from cop_thief.services.report.builder import build_report, report_to_json, validate_report_json
from cop_thief.shared.config import Config


def _result() -> FullGameResult:
    result = FullGameResult()
    for idx in range(1, 7):
        result.add(
            SubGameResult(
                index=idx,
                winner=Outcome.COP_WIN if idx % 2 else Outcome.THIEF_WIN,
                moves_used=idx + 2,
                barriers_used=idx % 3,
                score=SubGameScore(cop=20 if idx % 2 else 5, thief=5 if idx % 2 else 10),
            ),
        )
    return result


def test_report_builder_matches_contract(valid_config_yaml: object) -> None:
    cfg = Config.from_yaml(str(valid_config_yaml))
    data = build_report(cfg, _result())
    assert data["group_name"] == "TBD"
    assert data["cop_mcp_url"] == cfg.mcp.cop_url
    assert len(data["sub_games"]) == 6
    assert data["totals"] == {"cop": 75, "thief": 45}


def test_report_json_is_strict_parseable_json(valid_config_yaml: object) -> None:
    cfg = Config.from_yaml(str(valid_config_yaml))
    body = report_to_json(cfg, _result())
    assert body.strip().startswith("{")
    assert json.loads(body)["totals"]["cop"] == 75
    assert validate_report_json(body)["sub_games"][0]["moves"] == 3


def test_report_validation_rejects_extra_text() -> None:
    with pytest.raises(json.JSONDecodeError):
        validate_report_json('{"totals": {"cop": 1, "thief": 2}}\nthanks')
