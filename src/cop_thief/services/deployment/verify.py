"""Cloud MCP endpoint verification.

Traces: FR-MCP5, NFR-1, NFR-2, T-P7-06, T-P7-09, T-P7-10.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass
from typing import Any

from cop_thief.services.orchestrator._mcp_transport import call_remote_tool
from cop_thief.shared._gatekeeper_types import OutboundRequest
from cop_thief.shared.config import Config
from cop_thief.shared.gatekeeper import Gatekeeper

ToolCaller = Callable[[str, str, dict[str, Any]], Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class CloudVerification:
    """Outcome of public MCP endpoint checks."""

    cop_reachable: bool
    thief_reachable: bool
    cop_rejects_bad_token: bool
    thief_rejects_bad_token: bool
    revoked_token_rejected: bool | None

    @property
    def ok(self) -> bool:
        """Return True when all requested checks passed."""
        required = [
            self.cop_reachable,
            self.thief_reachable,
            self.cop_rejects_bad_token,
            self.thief_rejects_bad_token,
        ]
        if self.revoked_token_rejected is not None:
            required.append(self.revoked_token_rejected)
        return all(required)

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {**asdict(self), "ok": self.ok}


async def verify_cloud_endpoints(
    config: Config,
    cop_token: str,
    thief_token: str,
    *,
    revoked_token: str | None = None,
    caller: ToolCaller = call_remote_tool,
) -> CloudVerification:
    """Verify public MCP endpoints and token behavior."""
    gatekeeper = Gatekeeper(config.gatekeeper)
    cop_ok = await _expect_success(gatekeeper, caller, config.mcp.cop_url, cop_token)
    thief_ok = await _expect_success(gatekeeper, caller, config.mcp.thief_url, thief_token)
    cop_bad = await _expect_failure(gatekeeper, caller, config.mcp.cop_url, "bad-token")
    thief_bad = await _expect_failure(gatekeeper, caller, config.mcp.thief_url, "bad-token")
    revoked = None
    if revoked_token:
        revoked = await _expect_failure(gatekeeper, caller, config.mcp.cop_url, revoked_token)
    return CloudVerification(cop_ok, thief_ok, cop_bad, thief_bad, revoked)


async def _call(
    gatekeeper: Gatekeeper,
    caller: ToolCaller,
    base_url: str,
    token: str,
) -> dict[str, Any]:
    async def _fn() -> dict[str, Any]:
        return await caller(base_url, "game_status", {"token": token})

    response = await gatekeeper.call(OutboundRequest(target=base_url, fn=_fn))
    return response.result


async def _expect_success(
    gatekeeper: Gatekeeper,
    caller: ToolCaller,
    base_url: str,
    token: str,
) -> bool:
    try:
        await _call(gatekeeper, caller, base_url, token)
        return True
    except Exception:  # noqa: BLE001
        return False


async def _expect_failure(
    gatekeeper: Gatekeeper,
    caller: ToolCaller,
    base_url: str,
    token: str,
) -> bool:
    try:
        await _call(gatekeeper, caller, base_url, token)
        return False
    except Exception:  # noqa: BLE001
        return True
