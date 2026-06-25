"""Integration tests for Cop and Thief MCP servers."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from mcp import ClientSession
from mcp.client.sse import sse_client

COP_URL = "http://localhost:8001/sse"
THIEF_URL = "http://localhost:8002/sse"
COP_TOKEN = "integration-cop-token"
THIEF_TOKEN = "integration-thief-token"


@pytest.fixture(scope="module")
def run_servers(tmp_path_factory: pytest.TempPathFactory) -> object:
    """Start Cop and Thief servers as subprocesses for integration testing."""
    state_path = tmp_path_factory.mktemp("mcp-state") / "state.json"
    env = {
        **os.environ,
        "PYTHONPATH": "src",
        "MCP_COP_TOKEN": COP_TOKEN,
        "MCP_THIEF_TOKEN": THIEF_TOKEN,
        "MCP_STATE_PATH": str(state_path),
    }

    cop_proc = subprocess.Popen(
        [sys.executable, "-m", "cop_thief.mcp_servers.cop_server"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    thief_proc = subprocess.Popen(
        [sys.executable, "-m", "cop_thief.mcp_servers.thief_server"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait for both servers to be responsive using socket connections
    import socket

    ports = [8001, 8002]
    start = time.time()
    for port in ports:
        while time.time() - start < 15:
            try:
                with socket.create_connection(("localhost", port), timeout=1):
                    break
            except OSError:
                time.sleep(0.5)
        else:
            cop_proc.terminate()
            thief_proc.terminate()
            raise RuntimeError(f"MCP Server on port {port} failed to start within 15 seconds")

    yield

    for proc in (cop_proc, thief_proc):
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
    _cleanup_state(state_path)


def _cleanup_state(path: Path) -> None:
    """Remove integration-test state and lock files."""
    path.unlink(missing_ok=True)
    path.with_suffix(f"{path.suffix}.lock").unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_cop_server_tools(run_servers: object) -> None:
    """Test calling tools on the Cop MCP server."""
    async with (
        sse_client(COP_URL) as (read_stream, write_stream),
        ClientSession(read_stream, write_stream) as session,
    ):
        await session.initialize()

        # Verify position (happy path)
        res = await session.call_tool(
            "verify_position",
            {"agent": "cop", "token": COP_TOKEN},
        )
        assert res.isError is False
        assert res.content[0].text is not None

        # Verify unauthorized access rejected
        res_bad = await session.call_tool(
            "verify_position",
            {"agent": "cop", "token": "bad-token"},
        )
        assert res_bad.isError is True


@pytest.mark.asyncio
async def test_thief_server_tools(run_servers: object) -> None:
    """Test calling tools on the Thief MCP server."""
    async with (
        sse_client(THIEF_URL) as (read_stream, write_stream),
        ClientSession(read_stream, write_stream) as session,
    ):
        await session.initialize()

        # Verify position (happy path)
        res = await session.call_tool(
            "verify_position",
            {"agent": "thief", "token": THIEF_TOKEN},
        )
        assert res.isError is False
        assert res.content[0].text is not None

        # Thief server must reject place_barrier tool
        res_barrier = await session.call_tool(
            "place_barrier",
            {"token": THIEF_TOKEN},
        )
        assert res_barrier.isError is True
