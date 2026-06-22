"""CLI for verifying deployed MCP endpoints."""

from __future__ import annotations

import asyncio
import json

from cop_thief.services.deployment.verify import verify_cloud_endpoints
from cop_thief.shared.config import Config


def main() -> None:
    """Verify cloud MCP URLs from config and tokens from env."""
    config = Config.from_env()
    cop_token = Config.load_secret("MCP_COP_TOKEN") or ""
    thief_token = Config.load_secret("MCP_THIEF_TOKEN") or ""
    revoked = Config.load_secret("MCP_TEST_REVOKED_TOKEN", required=False)
    result = asyncio.run(
        verify_cloud_endpoints(config, cop_token, thief_token, revoked_token=revoked),
    )
    print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    if not result.ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
