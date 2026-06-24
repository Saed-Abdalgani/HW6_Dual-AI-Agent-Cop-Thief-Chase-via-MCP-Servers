"""SSE integration coverage for MCP barrier state."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from typing import Any

import pytest
from mcp import ClientSession
from mcp.client.sse import sse_client

COP_URL = "http://localhost:8001/sse"
THIEF_URL = "http://localhost:8002/sse"
COP_TOKEN = "sse-barrier-cop-token"
THIEF_TOKEN = "sse-barrier-thief-token"


@pytest.fixture(scope="module")
def run_barrier_servers(tmp_path_factory: pytest.TempPathFactory) -> object:
    """Start isolated Cop and Thief SSE servers."""
    state_path = tmp_path_factory.mktemp("mcp-barrier-state") / "state.json"
    env = {
        **os.environ,
        "PYTHONPATH": "src",
        "MCP_COP_TOKEN": COP_TOKEN,
        "MCP_THIEF_TOKEN": THIEF_TOKEN,
        "MCP_STATE_PATH": str(state_path),
    }
    procs = [
        subprocess.Popen(  # noqa: S603
            [sys.executable, "-m", module],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for module in ("cop_thief.mcp_servers.cop_server", "cop_thief.mcp_servers.thief_server")
    ]
    _wait_for_ports()
    yield
    for proc in procs:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
    state_path.unlink(missing_ok=True)
    state_path.with_suffix(f"{state_path.suffix}.lock").unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_place_barrier_updates_game_status_over_sse(run_barrier_servers: object) -> None:
    """Live SSE place_barrier updates barrier fields in game_status."""
    async with (
        sse_client(THIEF_URL) as (thief_read, thief_write),
        ClientSession(thief_read, thief_write) as thief_session,
        sse_client(COP_URL) as (cop_read, cop_write),
        ClientSession(cop_read, cop_write) as cop_session,
    ):
        await thief_session.initialize()
        await cop_session.initialize()
        thief_move = await thief_session.call_tool(
            "apply_action",
            {"agent": "thief", "action": "stay", "token": THIEF_TOKEN},
        )
        assert _tool_json(thief_move)["legal"] is True
        barrier = await cop_session.call_tool("place_barrier", {"token": COP_TOKEN})
        assert _tool_json(barrier)["state_delta"]["barrier_placed"] is True
        status = await cop_session.call_tool("game_status", {"token": COP_TOKEN})
        assert _tool_json(status)["barriers"] == [[0, 0]]


def _tool_json(result: object) -> dict[str, Any]:
    text = result.content[0].text  # type: ignore[attr-defined]
    assert text is not None
    parsed = json.loads(text)
    assert isinstance(parsed, dict)
    return parsed


def _wait_for_ports() -> None:
    import socket

    for port in (8001, 8002):
        deadline = time.time() + 15
        while time.time() < deadline:
            try:
                with socket.create_connection(("localhost", port), timeout=1):
                    break
            except OSError:
                time.sleep(0.5)
        else:
            raise RuntimeError(f"MCP Server on port {port} failed to start")
