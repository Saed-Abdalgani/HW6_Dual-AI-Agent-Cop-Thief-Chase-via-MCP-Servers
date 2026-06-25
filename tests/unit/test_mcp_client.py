"""Unit tests for McpClient health check with direct backend."""

from __future__ import annotations

import pytest

from cop_thief.mcp_servers import _state
from cop_thief.services.orchestrator._mcp_direct import DirectMcpBackend
from cop_thief.services.orchestrator.mcp_client import McpClient
from cop_thief.shared._gatekeeper_types import OutboundRequest, Response
from cop_thief.shared.auth import default_store
from cop_thief.shared.config import Config
from cop_thief.shared.gatekeeper import Gatekeeper


@pytest.fixture(autouse=True)
def _isolate_state(tmp_path: object, monkeypatch: pytest.MonkeyPatch) -> None:
    test_state = tmp_path / "mcp_state.json"  # type: ignore[operator]
    monkeypatch.setattr(_state, "STATE_PATH", test_state)


@pytest.mark.asyncio
async def test_mcp_health_check_direct(
    valid_config_yaml: object,
    minimal_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CONFIG_PATH", str(valid_config_yaml))
    cfg = Config.from_env()
    default_store.register_token("cop", "test-cop-token")
    default_store.register_token("thief", "test-thief-token")
    backend = DirectMcpBackend("test-cop-token", "test-thief-token")
    client = McpClient(
        cfg,
        Gatekeeper(cfg.gatekeeper),
        "test-cop-token",
        "test-thief-token",
        backend=backend,
    )
    status = await client.health_check()
    assert status.cop_mcp is True
    assert status.thief_mcp is True


@pytest.mark.asyncio
async def test_direct_mcp_calls_route_through_gatekeeper(
    valid_config_yaml: object,
    minimal_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Direct local MCP still uses Gatekeeper rate-limit/retry plumbing."""
    monkeypatch.setenv("CONFIG_PATH", str(valid_config_yaml))
    cfg = Config.from_env()
    default_store.register_token("cop", "gatekeeper-cop-token")
    default_store.register_token("thief", "gatekeeper-thief-token")

    class RecordingGatekeeper:
        def __init__(self) -> None:
            self.requests: list[OutboundRequest] = []

        async def call(self, request: OutboundRequest) -> Response:
            self.requests.append(request)
            result = await request.fn()
            return Response(
                target=request.target,
                result=result,
                latency_s=0.0,
                attempts=1,
            )

    gatekeeper = RecordingGatekeeper()
    client = McpClient(
        cfg,
        gatekeeper,  # type: ignore[arg-type]
        "gatekeeper-cop-token",
        "gatekeeper-thief-token",
        backend=DirectMcpBackend("gatekeeper-cop-token", "gatekeeper-thief-token"),
    )

    status = await client.game_status()

    assert status["barriers"] == []
    assert len(gatekeeper.requests) == 1
    request = gatekeeper.requests[0]
    assert request.target == "mcp-direct:cop"
    assert request.metadata == {"server": "cop", "tool": "game_status", "direct": True}
