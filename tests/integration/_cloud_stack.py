"""Helpers for local cloud-style MCP integration tests."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import textwrap
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from cop_thief.mcp_servers._state_backend import reset_state_backend
from cop_thief.shared.auth import default_store

COP_PORT = 8101
THIEF_PORT = 8102
COP_TOKEN = "cloud-cop-token"
THIEF_TOKEN = "cloud-thief-token"
REVOKED_TOKEN = "cloud-revoked-token"


@contextmanager
def start_cloud_stack(root: Path) -> Iterator[dict[str, str]]:
    """Start cop/thief MCP servers with shared file state."""
    root.mkdir(parents=True, exist_ok=True)
    config_path = root / "config.yaml"
    state_file = root / "mcp_state.json"
    config_path.write_text(_config(root), encoding="utf-8")
    for port in (COP_PORT, THIEF_PORT):
        _free_port(port)
    procs = _start_processes(config_path, state_file)
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


def _start_processes(config_path: Path, state_file: Path) -> list[subprocess.Popen[bytes]]:
    env = {
        **os.environ,
        "PYTHONPATH": "src",
        "CONFIG_PATH": str(config_path),
        "MCP_STATE_PATH": str(state_file),
        "MCP_COP_TOKEN": COP_TOKEN,
        "MCP_THIEF_TOKEN": THIEF_TOKEN,
        "MCP_REVOKED_TOKENS": REVOKED_TOKEN,
        "LLM_API_KEY": "test-key",
    }
    env.pop("MCP_STATE_URL", None)
    return [
        subprocess.Popen(  # noqa: S603
            [sys.executable, "-m", module],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for module in ("cop_thief.mcp_servers.cop_server", "cop_thief.mcp_servers.thief_server")
    ]


def _config(root: Path) -> str:
    return textwrap.dedent(
        f"""\
        grid_size: [5, 5]
        max_moves: 2
        num_games: 1
        max_barriers: 1
        scoring: {{ cop_win: 20, thief_win: 10, cop_loss: 5, thief_loss: 5 }}
        start_mode: random
        thief_moves_first: true
        discount_gamma: 0.95
        strategy: heuristic
        llm: {{ provider: openai, model: gpt-4o-mini, timeout_s: 30 }}
        mcp:
          mode: http
          auto_launch: false
          cop_url: "http://127.0.0.1:{COP_PORT}"
          thief_url: "http://127.0.0.1:{THIEF_PORT}"
        gatekeeper: {{ rate_limit_per_target: 100, max_retries: 1, queue_size: 64, timeout_s: 30 }}
        email: {{ to: "test@example.com" }}
        nlp: {{ tone: balanced, transcript_dir: "{(root / 'results').as_posix()}" }}
        timezone: "UTC"
        seed: 11
        """
    )


def _free_port(port: int) -> None:
    if sys.platform != "win32":
        return
    try:
        out = subprocess.check_output(["netstat", "-ano"], text=True, errors="ignore")
        for line in out.splitlines():
            if f":{port} " in line and "LISTENING" in line:
                subprocess.run(["taskkill", "/F", "/PID", line.split()[-1]], check=False)  # noqa: S603
    except (OSError, ValueError, subprocess.SubprocessError):
        return


def _wait_for_port(port: int, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return
        except OSError:
            time.sleep(0.25)
    raise RuntimeError(f"Port {port} did not open within {timeout}s.")
