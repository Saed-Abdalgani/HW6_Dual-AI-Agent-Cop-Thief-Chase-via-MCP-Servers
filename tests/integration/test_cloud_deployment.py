"""Integration tests for Phase P7 cloud-style remote MCP deployment."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import textwrap
import time

import pytest
from mcp import ClientSession
from mcp.client.sse import sse_client

from cop_thief.mcp_servers._state_backend import reset_state_backend
from cop_thief.sdk.facade import CopThiefSDK
from cop_thief.shared.auth import default_store
from cop_thief.shared.config import Config

COP_PORT = 8101
THIEF_PORT = 8102
COP_TOKEN = "cloud-cop-token"
THIEF_TOKEN = "cloud-thief-token"
REVOKED_TOKEN = "cloud-revoked-token"


def _free_port(port: int) -> None:
    """Terminate any process listening on *port* (best-effort, Windows-friendly)."""
    if sys.platform != "win32":
        return
    try:
        import subprocess as sp

        out = sp.check_output(["netstat", "-ano"], text=True, errors="ignore")
        for line in out.splitlines():
            if f":{port} " in line and "LISTENING" in line:
                pid = int(line.split()[-1])
                if pid > 0:
                    sp.run(["taskkill", "/F", "/PID", str(pid)], check=False)  # noqa: S603
    except (OSError, ValueError, subprocess.SubprocessError):
        return


def _wait_for_port(port: int, timeout: float = 20.0) -> None:
    host = "127.0.0.1"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except OSError:
            time.sleep(0.25)
    msg = f"Port {port} did not open within {timeout}s."
    raise RuntimeError(msg)


@pytest.fixture(scope="module")
def cloud_stack(tmp_path_factory: pytest.TempPathFactory) -> dict[str, str]:
    """Start cop/thief MCP servers with shared file state for remote integration tests."""
    root = tmp_path_factory.mktemp("cloud")
    state_file = root / "mcp_state.json"
    cfg = textwrap.dedent(
        f"""\
        grid_size: [5, 5]
        max_moves: 2
        num_games: 1
        max_barriers: 1
        scoring:
          cop_win: 20
          thief_win: 10
          cop_loss: 5
          thief_loss: 5
        start_mode: random
        thief_moves_first: true
        discount_gamma: 0.95
        strategy: heuristic
        llm:
          provider: openai
          model: gpt-4o-mini
          timeout_s: 30
        mcp:
          cop_url: "http://127.0.0.1:{COP_PORT}"
          thief_url: "http://127.0.0.1:{THIEF_PORT}"
        gatekeeper:
          rate_limit_per_target: 100
          max_retries: 1
          queue_size: 64
          timeout_s: 30
        email:
          to: "test@example.com"
        nlp:
          tone: balanced
          transcript_dir: "{(root / 'results').as_posix()}"
        timezone: "UTC"
        seed: 11
        """
    )
    config_path = root / "config.yaml"
    config_path.write_text(cfg, encoding="utf-8")
    for port in (COP_PORT, THIEF_PORT):
        _free_port(port)
    base_env = {
        **os.environ,
        "PYTHONPATH": "src",
        "CONFIG_PATH": str(config_path),
        "MCP_STATE_PATH": str(state_file),
        "MCP_COP_TOKEN": COP_TOKEN,
        "MCP_THIEF_TOKEN": THIEF_TOKEN,
        "MCP_REVOKED_TOKENS": REVOKED_TOKEN,
        "LLM_API_KEY": "test-key",
    }
    base_env.pop("MCP_STATE_URL", None)
    procs = [
        subprocess.Popen(  # noqa: S603
            [sys.executable, "-m", "cop_thief.mcp_servers.cop_server"],
            env=base_env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ),
        subprocess.Popen(  # noqa: S603
            [sys.executable, "-m", "cop_thief.mcp_servers.thief_server"],
            env=base_env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ),
    ]
    try:
        for port in (COP_PORT, THIEF_PORT):
            _wait_for_port(port)
        time.sleep(1.0)
        default_store.register_token("cop", COP_TOKEN)
        default_store.register_token("thief", THIEF_TOKEN)
        yield {"config_path": str(config_path)}
    finally:
        for proc in procs:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
        reset_state_backend()


async def _mock_llm(prompt: str) -> str:
    return json.dumps({"action": "stay", "nl_message": "Cloud chase in progress."})


async def _call_tool(url: str, tool: str, args: dict) -> object:
    async with sse_client(url) as streams, ClientSession(streams[0], streams[1]) as session:
        await session.initialize()
        return await session.call_tool(tool, args)


@pytest.mark.asyncio
async def test_cloud_security_rejects_bad_and_revoked_tokens(cloud_stack: dict[str, str]) -> None:
    """T-P7-10: unauthenticated and revoked tokens fail on both remote endpoints."""
    del cloud_stack
    checks = (
        (f"http://127.0.0.1:{COP_PORT}/sse", "cop", COP_TOKEN),
        (f"http://127.0.0.1:{THIEF_PORT}/sse", "thief", THIEF_TOKEN),
    )
    for url, agent, good_token in checks:
        ok = await _call_tool(
            url,
            "verify_position",
            {"agent": agent, "token": good_token},
        )
        assert ok.isError is False
        bad = await _call_tool(
            url,
            "verify_position",
            {"agent": agent, "token": "bad-token"},
        )
        assert bad.isError is True
        revoked = await _call_tool(
            url,
            "verify_position",
            {"agent": agent, "token": REVOKED_TOKEN},
        )
        assert revoked.isError is True


def test_cloud_remote_mcp_sub_game(
    cloud_stack: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
    minimal_env: None,
) -> None:
    """T-P7-09: sub-game completes over remote MCP URLs (mocked LLM)."""
    monkeypatch.setenv("CONFIG_PATH", cloud_stack["config_path"])
    monkeypatch.delenv("MCP_STATE_URL", raising=False)
    reset_state_backend()
    config = Config.from_env()
    sdk = CopThiefSDK(config, use_direct_mcp=False, llm_caller=_mock_llm)
    result = sdk.run_sub_game(1)
    assert result.winner.value in {"cop_win", "thief_win"}


@pytest.mark.live_cloud
@pytest.mark.asyncio
async def test_live_cloud_endpoints_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    """Optional live check when MCP_COP_URL/MCP_THIEF_URL env vars point at production."""
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
