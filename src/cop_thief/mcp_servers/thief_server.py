"""Thief MCP Server exposing tools only.

Traces: FR-MCP1, FR-MCP5, FR-C1, T-P2-11, T-P2-12.
"""

from __future__ import annotations

from fastmcp import FastMCP

from cop_thief.mcp_servers import tools
from cop_thief.mcp_servers.runtime import bind_host_port, seed_tokens_from_env
from cop_thief.shared.config import Config

mcp = FastMCP("Thief Server")

seed_tokens_from_env()


@mcp.tool()
def send_message(from_agent: str, text: str, token: str) -> dict:
    """Send a free-text message to the opponent."""
    return tools.send_message(from_agent, text, token)


@mcp.tool()
def receive_message(for_agent: str, token: str) -> dict:
    """Receive the latest message from the opponent."""
    return tools.receive_message(for_agent, token)


@mcp.tool()
def update_position(agent: str, pos: list[int], token: str) -> dict:
    """Update position of the agent on the board."""
    return tools.update_position(agent, pos, token)


@mcp.tool()
def verify_position(agent: str, token: str) -> dict:
    """Get the current position of the agent."""
    return tools.verify_position(agent, token)


@mcp.tool()
def choose_action(agent: str, observation: dict, token: str) -> dict:
    """Get a legal action based on the agent's observation."""
    return tools.choose_action(agent, observation, token)


@mcp.tool()
def apply_action(agent: str, action: str, token: str) -> dict:
    """Apply the action and return state delta."""
    if action == "place_barrier":
        return {"legal": False, "rejection_reason": "Thief cannot place barriers."}
    return tools.apply_action(agent, action, token)


@mcp.tool()
def game_status(token: str) -> dict:
    """Get current game status snapshot."""
    return tools.game_status(token)


if __name__ == "__main__":
    cfg = Config.from_env()
    host, port = bind_host_port(cfg, "thief")
    mcp.run(transport="sse", host=host, port=port)
