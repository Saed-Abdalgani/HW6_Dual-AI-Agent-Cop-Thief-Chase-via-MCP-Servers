"""Test that MCP server modules import successfully and register all tools."""

from __future__ import annotations

import pytest

from cop_thief.mcp_servers.cop_server import mcp as cop_mcp
from cop_thief.mcp_servers.thief_server import mcp as thief_mcp


@pytest.mark.asyncio
async def test_cop_server_tools_registered() -> None:
    """Ensure Cop MCP server registers correct tools."""
    tools = [t.name for t in await cop_mcp.list_tools()]
    assert "send_message" in tools
    assert "receive_message" in tools
    assert "update_position" in tools
    assert "verify_position" in tools
    assert "choose_action" in tools
    assert "apply_action" in tools
    assert "game_status" in tools
    assert "place_barrier" in tools


@pytest.mark.asyncio
async def test_thief_server_tools_registered() -> None:
    """Ensure Thief MCP server registers correct tools."""
    tools = [t.name for t in await thief_mcp.list_tools()]
    assert "send_message" in tools
    assert "receive_message" in tools
    assert "update_position" in tools
    assert "verify_position" in tools
    assert "choose_action" in tools
    assert "apply_action" in tools
    assert "game_status" in tools
    assert "place_barrier" not in tools
