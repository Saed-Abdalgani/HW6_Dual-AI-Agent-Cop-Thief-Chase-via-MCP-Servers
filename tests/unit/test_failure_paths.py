"""Edge and failure-path tests for LLM, MCP, and Gmail externals."""

from __future__ import annotations

from typing import Any

import pytest

from cop_thief.constants import Agent
from cop_thief.services.orchestrator._types import Observation
from cop_thief.services.orchestrator.llm_client import LlmClient
from cop_thief.services.orchestrator.mcp_client import McpClient
from cop_thief.services.report.builder import validate_report_json
from cop_thief.services.report.emailer import GmailReportEmailer
from cop_thief.shared._gatekeeper_types import OutboundRequest
from cop_thief.shared.config import Config
from cop_thief.shared.gatekeeper import Gatekeeper


class _FailingMcpBackend:
    async def call_tool(
        self,
        server: str,
        tool: str,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        raise ConnectionError(f"{server} MCP unreachable")


@pytest.mark.asyncio
async def test_llm_raises_uses_heuristic_fallback(
    valid_config_yaml: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CONFIG_PATH", str(valid_config_yaml))

    async def exploding(_prompt: str) -> str:
        raise TimeoutError("LLM timeout")

    cfg = Config.from_env()
    client = LlmClient(cfg, Gatekeeper(cfg.gatekeeper), llm_caller=exploding)
    obs = Observation(
        agent=Agent.THIEF,
        own_pos=(2, 2),
        opp_estimate=(0, 0),
        barriers=frozenset(),
        barriers_used=0,
        max_barriers=5,
        grid_size=(5, 5),
        move_count=0,
    )
    decision = await client.decide(obs)
    assert decision.nl_message
    assert decision.action is not None


@pytest.mark.asyncio
async def test_llm_health_check_false_on_failure(
    valid_config_yaml: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CONFIG_PATH", str(valid_config_yaml))

    async def exploding(_prompt: str) -> str:
        raise RuntimeError("provider down")

    cfg = Config.from_env()
    client = LlmClient(cfg, Gatekeeper(cfg.gatekeeper), llm_caller=exploding)
    assert await client.health_check() is False


@pytest.mark.asyncio
async def test_mcp_health_check_marks_unreachable(
    valid_config_yaml: object,
    minimal_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CONFIG_PATH", str(valid_config_yaml))
    cfg = Config.from_env()
    client = McpClient(
        cfg,
        Gatekeeper(cfg.gatekeeper),
        "cop-token",
        "thief-token",
        backend=_FailingMcpBackend(),
    )
    status = await client.health_check()
    assert status.cop_mcp is False
    assert status.thief_mcp is False


@pytest.mark.asyncio
async def test_gmail_emailer_returns_error_on_gatekeeper_failure(
    valid_config_yaml: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = Config.from_yaml(str(valid_config_yaml))
    monkeypatch.setenv("GMAIL_ACCESS_TOKEN", "token")

    class BrokenGatekeeper(Gatekeeper):
        async def call(self, request: OutboundRequest) -> object:
            raise RuntimeError("Gmail quota exceeded")

    emailer = GmailReportEmailer(cfg, BrokenGatekeeper(cfg.gatekeeper))
    result = await emailer.send('{"ok":true}')
    assert result.sent is False
    assert "quota" in result.error.lower()


def test_report_validation_rejects_bad_totals() -> None:
    body = (
        '{"group_name":"g","students":[],"github_repo":"r",'
        '"cop_mcp_url":"c","thief_mcp_url":"t","timezone":"UTC",'
        '"sub_games":[],"totals":{"cop":1}}'
    )
    with pytest.raises(ValueError, match="totals"):
        validate_report_json(body)
