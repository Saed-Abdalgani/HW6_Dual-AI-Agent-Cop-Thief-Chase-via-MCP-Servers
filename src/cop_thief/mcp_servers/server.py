"""Role-selected MCP server entrypoint for cloud deployments.

Set ``SERVER_ROLE=cop`` or ``SERVER_ROLE=thief``.
"""

from __future__ import annotations

from cop_thief.mcp_servers.cop_server import mcp as cop_mcp
from cop_thief.mcp_servers.runtime import bind_host_port, role_from_env
from cop_thief.mcp_servers.thief_server import mcp as thief_mcp
from cop_thief.shared.config import Config


def main() -> None:
    """Run the selected MCP server over SSE."""
    cfg = Config.from_env()
    role = role_from_env()
    host, port = bind_host_port(cfg, role)
    mcp = cop_mcp if role == "cop" else thief_mcp
    mcp.run(transport="sse", host=host, port=port)


if __name__ == "__main__":
    main()
