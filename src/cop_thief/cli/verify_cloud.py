"""CLI for verifying deployed MCP endpoints."""

from __future__ import annotations

import asyncio
import json
import sys

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
        if not result.cop_reachable or not result.thief_reachable:
            print(  # noqa: T201
                "\nHint: servers unreachable. On the VPS run:\n"
                "  bash deploy/vps/fix-server.sh\n"
                "Also open GCP firewall TCP 8001,8002,8090 (Ingress, 0.0.0.0/0).",
                file=sys.stderr,
            )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
