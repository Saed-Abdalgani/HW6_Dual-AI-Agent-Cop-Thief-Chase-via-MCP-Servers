"""Tests for Phase P7 cloud endpoint verifier."""

from __future__ import annotations

from typing import Any

import pytest

from cop_thief.services.deployment.verify import verify_cloud_endpoints
from cop_thief.shared.config import Config


@pytest.mark.asyncio
async def test_verify_cloud_endpoints_all_green(valid_config_yaml: object) -> None:
    cfg = Config.from_yaml(str(valid_config_yaml))

    async def caller(base_url: str, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        if args["token"] in {"good-cop", "good-thief"}:
            return {"ok": True, "url": base_url, "tool": tool}
        raise RuntimeError("Unauthorized")

    result = await verify_cloud_endpoints(
        cfg,
        "good-cop",
        "good-thief",
        revoked_token="old-token",
        caller=caller,
    )
    assert result.ok is True
    assert result.as_dict()["revoked_token_rejected"] is True


@pytest.mark.asyncio
async def test_verify_cloud_endpoints_detects_reachable_failure(valid_config_yaml: object) -> None:
    cfg = Config.from_yaml(str(valid_config_yaml))

    async def caller(base_url: str, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(f"{base_url}:{tool}:{args['token']}")

    result = await verify_cloud_endpoints(cfg, "good-cop", "good-thief", caller=caller)
    assert result.ok is False
    assert result.cop_reachable is False
    assert result.cop_rejects_bad_token is True
