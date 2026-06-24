"""Integration tests for Phase P7 cloud-style remote MCP deployment."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from mcp import ClientSession
from mcp.client.sse import sse_client

from cop_thief.mcp_servers._state_backend import reset_state_backend
from cop_thief.sdk.facade import CopThiefSDK
from cop_thief.shared.config import Config
from tests.integration._cloud_stack import (
    COP_PORT,
    COP_TOKEN,
    REVOKED_TOKEN,
    THIEF_PORT,
    THIEF_TOKEN,
    start_cloud_stack,
)


async def _mock_llm(_prompt: str) -> str:
    return json.dumps({"action": "stay", "nl_message": "Cloud chase in progress."})


async def _call_tool(url: str, tool: str, args: dict) -> object:
    async with sse_client(url) as streams, ClientSession(streams[0], streams[1]) as session:
        await session.initialize()
        return await session.call_tool(tool, args)


@pytest.mark.asyncio
async def test_cloud_security_rejects_bad_and_revoked_tokens(tmp_path: Path) -> None:
    """T-P7-10: unauthenticated and revoked tokens fail on both remote endpoints."""
    with start_cloud_stack(tmp_path):
        checks = (
            (f"http://127.0.0.1:{COP_PORT}/sse", "cop", COP_TOKEN),
            (f"http://127.0.0.1:{THIEF_PORT}/sse", "thief", THIEF_TOKEN),
        )
        for url, agent, good_token in checks:
            ok = await _call_tool(url, "verify_position", {"agent": agent, "token": good_token})
            bad = await _call_tool(url, "verify_position", {"agent": agent, "token": "bad-token"})
            revoked = await _call_tool(
                url,
                "verify_position",
                {"agent": agent, "token": REVOKED_TOKEN},
            )
            assert ok.isError is False
            assert bad.isError is True
            assert revoked.isError is True


def test_cloud_remote_mcp_sub_game(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    minimal_env: None,
) -> None:
    """T-P7-09: sub-game completes over remote MCP URLs (mocked LLM)."""
    with start_cloud_stack(tmp_path) as stack:
        monkeypatch.setenv("CONFIG_PATH", stack["config_path"])
        monkeypatch.delenv("MCP_STATE_URL", raising=False)
        reset_state_backend()
        sdk = CopThiefSDK(Config.from_env(), use_direct_mcp=False, llm_caller=_mock_llm)
        result = sdk.run_sub_game(1)
        assert result.winner.value in {"cop_win", "thief_win"}


@pytest.mark.live_cloud
@pytest.mark.asyncio
async def test_live_cloud_endpoints_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    """Optional live check when MCP_COP_URL/MCP_THIEF_URL point at production."""
    if not os.environ.get("MCP_COP_URL") or not os.environ.get("MCP_THIEF_URL"):
        pytest.skip("Live cloud URLs not configured.")
    from cop_thief.services.deployment.verify import verify_cloud_endpoints

    monkeypatch.setenv("CONFIG_PATH", "config/config.cloud.yaml")
    cfg = Config.from_env()
    result = await verify_cloud_endpoints(
        cfg,
        Config.load_secret("MCP_COP_TOKEN") or "",
        Config.load_secret("MCP_THIEF_TOKEN") or "",
        revoked_token=Config.load_secret("MCP_TEST_REVOKED_TOKEN", required=False),
    )
    assert result.ok is True
