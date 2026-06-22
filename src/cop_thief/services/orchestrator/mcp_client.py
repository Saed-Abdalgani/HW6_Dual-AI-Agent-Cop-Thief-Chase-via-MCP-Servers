"""MCP client wrapping cop and thief tool calls via Gatekeeper.

Traces: FR-O2, NFR-5, T-P3-01, T-P3-02.
"""

from __future__ import annotations

from typing import Any, Literal, Protocol

from cop_thief.services.orchestrator._mcp_direct import DirectMcpBackend
from cop_thief.services.orchestrator._mcp_transport import call_remote_tool
from cop_thief.services.orchestrator._types import HealthStatus
from cop_thief.shared._gatekeeper_types import OutboundRequest
from cop_thief.shared.config import Config
from cop_thief.shared.gatekeeper import Gatekeeper

ServerName = Literal["cop", "thief"]


class McpBackend(Protocol):
    """Protocol for pluggable MCP tool invocation."""

    async def call_tool(
        self, server: ServerName, tool: str, args: dict[str, Any],
    ) -> dict[str, Any]:
        """Invoke *tool* on *server* and return the result dict."""
        ...


class McpClient:
    """High-level MCP tool client for cop and thief servers."""

    def __init__(
        self,
        config: Config,
        gatekeeper: Gatekeeper,
        cop_token: str,
        thief_token: str,
        backend: McpBackend | None = None,
    ) -> None:
        """Wire URLs, tokens, and optional in-process backend."""
        self._cfg = config
        self._gk = gatekeeper
        self._cop_token = cop_token
        self._thief_token = thief_token
        self._backend = backend or DirectMcpBackend(cop_token, thief_token)

    def _url(self, server: ServerName) -> str:
        return self._cfg.mcp.cop_url if server == "cop" else self._cfg.mcp.thief_url

    def _token(self, server: ServerName) -> str:
        return self._cop_token if server == "cop" else self._thief_token

    async def _invoke(
        self, server: ServerName, tool: str, args: dict[str, Any],
    ) -> dict[str, Any]:
        target = f"{server}_mcp"

        async def _remote() -> dict[str, Any]:
            merged = {**args, "token": self._token(server)}
            return await call_remote_tool(self._url(server), tool, merged)

        async def _fn() -> dict[str, Any]:
            if isinstance(self._backend, DirectMcpBackend):
                return await self._backend.call_tool(server, tool, args)
            return await _remote()

        if isinstance(self._backend, DirectMcpBackend):
            return await _fn()
        resp = await self._gk.call(OutboundRequest(target=target, fn=_fn))
        return resp.result

    async def send_message(self, from_agent: str, text: str) -> dict[str, Any]:
        """Send a free-text NL message from *from_agent*."""
        server: ServerName = "cop" if from_agent == "cop" else "thief"
        return await self._invoke(server, "send_message", {"from_agent": from_agent, "text": text})

    async def receive_message(self, for_agent: str) -> dict[str, Any]:
        """Receive the latest NL message for *for_agent*."""
        server: ServerName = "cop" if for_agent == "cop" else "thief"
        return await self._invoke(server, "receive_message", {"for_agent": for_agent})

    async def verify_position(self, agent: str) -> dict[str, Any]:
        """Return the agent's current position."""
        server: ServerName = "cop" if agent == "cop" else "thief"
        return await self._invoke(server, "verify_position", {"agent": agent})

    async def apply_action(self, agent: str, action: str) -> dict[str, Any]:
        """Apply *action* for *agent* on the MCP server engine."""
        server: ServerName = "cop" if agent == "cop" else "thief"
        return await self._invoke(server, "apply_action", {"agent": agent, "action": action})

    async def game_status(self) -> dict[str, Any]:
        """Return the current game status snapshot (cop token)."""
        return await self._invoke("cop", "game_status", {})

    async def update_position(self, agent: str, pos: tuple[int, int]) -> dict[str, Any]:
        """Set *agent* position (used for sub-game reset)."""
        server: ServerName = "cop" if agent == "cop" else "thief"
        return await self._invoke(server, "update_position", {"agent": agent, "pos": list(pos)})

    async def health_check(self) -> HealthStatus:
        """Probe cop and thief MCP reachability."""
        status = HealthStatus()
        for server in ("cop", "thief"):
            try:
                await self._invoke(server, "game_status", {})
                setattr(status, f"{server}_mcp", True)
            except Exception:  # noqa: BLE001, S110
                pass
        return status
