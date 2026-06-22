"""Spawn local MCP server subprocesses for autonomous CLI runs.

Traces: T-P3-14, AC-2.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from contextlib import AbstractContextManager
from typing import Self

from cop_thief.shared.config import Config


def _wait_for_port(host: str, port: int, timeout: float = 15.0) -> bool:
    """Return True when *port* accepts TCP connections."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.3)
    return False


class McpServerLauncher(AbstractContextManager["McpServerLauncher"]):
    """Start cop and thief MCP servers as background subprocesses."""

    def __init__(self, config: Config) -> None:
        """Store config and process handles."""
        self._cfg = config
        self._procs: list[subprocess.Popen[bytes]] = []

    def start(self) -> None:
        """Launch both servers and wait until ports are open."""
        from urllib.parse import urlparse

        env = {**os.environ, "PYTHONPATH": "src"}
        modules = [
            ("cop_thief.mcp_servers.cop_server", self._cfg.mcp.cop_url),
            ("cop_thief.mcp_servers.thief_server", self._cfg.mcp.thief_url),
        ]
        for module, url in modules:
            proc = subprocess.Popen(  # noqa: S603
                [sys.executable, "-m", module],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._procs.append(proc)
            parsed = urlparse(url)
            host = parsed.hostname or "localhost"
            port = parsed.port or 8001
            if not _wait_for_port(host, port):
                self.stop()
                msg = f"MCP server {module} failed to start on {host}:{port}."
                raise RuntimeError(msg)

    def stop(self) -> None:
        """Terminate all spawned server processes."""
        for proc in self._procs:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
        self._procs.clear()

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.stop()
