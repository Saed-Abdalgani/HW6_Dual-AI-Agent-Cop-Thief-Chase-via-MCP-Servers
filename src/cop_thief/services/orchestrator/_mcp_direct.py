"""Direct in-process MCP tool backend for tests and local runs.

Calls :mod:`cop_thief.mcp_servers.tools` without HTTP.  Used when MCP
servers are not running or in unit/integration tests with mocks.

Traces: T-P3-01, T-P3-15.
"""

from __future__ import annotations

from typing import Any, Literal

from cop_thief.mcp_servers import tools

ServerName = Literal["cop", "thief"]


class DirectMcpBackend:
    """Invoke MCP tools in-process (no network)."""

    def __init__(self, cop_token: str, thief_token: str) -> None:
        """Store per-agent bearer tokens."""
        self._tokens = {"cop": cop_token, "thief": thief_token}

    async def call_tool(
        self,
        server: ServerName,
        tool: str,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """Dispatch *tool* on the given server using registered tokens."""
        token = self._tokens[server]
        merged = {**args, "token": token}
        dispatch: dict[str, object] = {
            "send_message": lambda: tools.send_message(
                merged["from_agent"],
                merged["text"],
                token,
            ),
            "receive_message": lambda: tools.receive_message(
                merged["for_agent"],
                token,
            ),
            "update_position": lambda: tools.update_position(
                merged["agent"],
                merged["pos"],
                token,
            ),
            "verify_position": lambda: tools.verify_position(merged["agent"], token),
            "choose_action": lambda: tools.choose_action(
                merged["agent"],
                merged.get("observation", {}),
                token,
            ),
            "apply_action": lambda: tools.apply_action(
                merged["agent"],
                merged["action"],
                token,
            ),
            "game_status": lambda: tools.game_status(token),
            "place_barrier": lambda: tools.apply_action("cop", "place_barrier", token),
        }
        handler = dispatch.get(tool)
        if handler is None:
            msg = f"Unknown MCP tool '{tool}'."
            raise ValueError(msg)
        result = handler()
        return result  # type: ignore[return-value]
