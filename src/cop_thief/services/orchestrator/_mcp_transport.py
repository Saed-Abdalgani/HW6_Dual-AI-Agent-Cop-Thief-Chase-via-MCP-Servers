"""HTTP/SSE transport for remote MCP tool calls.

Traces: T-P3-01, PLAN §9.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from mcp import ClientSession
from mcp.client.sse import sse_client

ServerName = Literal["cop", "thief"]


def _sse_url(base_url: str) -> str:
    """Build the SSE endpoint URL from a configured MCP base URL."""
    return f"{base_url.rstrip('/')}/sse"


def _parse_tool_result(result: object) -> dict[str, Any]:
    """Convert an MCP tool result payload into a plain dict."""
    if hasattr(result, "isError") and result.isError:  # noqa: SIM102
        text = result.content[0].text if result.content else "MCP tool error"
        raise RuntimeError(text)
    if not result.content:
        return {}
    text = result.content[0].text
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {"result": parsed}
    except json.JSONDecodeError:
        return {"text": text}


async def call_remote_tool(
    base_url: str,
    tool: str,
    args: dict[str, Any],
) -> dict[str, Any]:
    """Call *tool* on an MCP server reachable at *base_url*."""
    async with sse_client(_sse_url(base_url)) as streams, ClientSession(
        streams[0], streams[1],
    ) as session:
        await session.initialize()
        result = await session.call_tool(tool, args)
        return _parse_tool_result(result)
