"""Minimal bearer-protected JSON store for shared MCP game state.

Traces: FR-MCP5, T-P7-02, T-P7-03.
"""

from __future__ import annotations

import json
import os
import socketserver
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import ClassVar

from cop_thief.shared._config_loader import load_secret


class _StateHandler(BaseHTTPRequestHandler):
    """Serve GET/PUT for a single in-memory JSON blob."""

    protocol_version = "HTTP/1.0"
    store: ClassVar[dict | None] = None
    token: ClassVar[str] = ""

    def log_message(self, format: str, *args: object) -> None:
        """Suppress default access logging."""

    def _authorized(self) -> bool:
        auth = self.headers.get("Authorization", "")
        return auth == f"Bearer {self.token}"

    def do_GET(self) -> None:
        if not self._authorized():
            self.send_error(401, "Unauthorized")
            return
        if _StateHandler.store is None:
            self.send_error(404, "No state")
            return
        body = json.dumps(_StateHandler.store).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_PUT(self) -> None:
        if not self._authorized():
            self.send_error(401, "Unauthorized")
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        _StateHandler.store = json.loads(raw)
        self.send_response(204)
        self.end_headers()


class _ReuseHTTPServer(HTTPServer):
    allow_reuse_address = True


def main() -> None:
    """Run the shared state HTTP service."""
    host = os.environ.get("MCP_STATE_HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", os.environ.get("MCP_STATE_PORT", "8090")))
    _StateHandler.token = load_secret("MCP_STATE_TOKEN") or ""
    with _ReuseHTTPServer((host, port), _StateHandler) as server:
        if hasattr(socketserver.ThreadingMixIn, "daemon_threads"):
            server.daemon_threads = True
        server.serve_forever()


if __name__ == "__main__":
    main()
