"""Gatekeeper success and retry tests — T-P0-24 (part 1/2).

Covers:
- Successful call returns a Response with correct fields.
- Target label is echoed in the response.
- Transient failures are retried up to max_retries and then succeed.
- All attempts exhausted raises GatekeeperRetryExhaustedError.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from cop_thief.shared.config import GatekeeperConfig
from cop_thief.shared.gatekeeper import (
    Gatekeeper,
    GatekeeperRetryExhaustedError,
    OutboundRequest,
    Response,
)

# ---------------------------------------------------------------------------
# Helpers (shared between test modules via module-level functions)
# ---------------------------------------------------------------------------


def make_cfg(
    *,
    rate: float = 100.0,
    retries: int = 2,
    queue: int = 64,
    timeout: int = 5,
) -> GatekeeperConfig:
    """Build a :class:`GatekeeperConfig` with convenient keyword overrides."""
    return GatekeeperConfig(
        rate_limit_per_target=rate,
        max_retries=retries,
        queue_size=queue,
        timeout_s=timeout,
    )


def make_request(fn: object, target: str = "test") -> OutboundRequest:
    """Wrap *fn* in an :class:`OutboundRequest`."""
    return OutboundRequest(target=target, fn=fn)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Success path
# ---------------------------------------------------------------------------


class TestGatekeeperSuccess:
    @pytest.mark.asyncio
    async def test_successful_call_returns_response(self) -> None:
        gk = Gatekeeper(make_cfg())
        fn = AsyncMock(return_value={"ok": True})
        resp = await gk.call(make_request(fn))
        assert isinstance(resp, Response)
        assert resp.result == {"ok": True}
        assert resp.attempts == 1
        assert resp.latency_s >= 0

    @pytest.mark.asyncio
    async def test_target_label_echoed_in_response(self) -> None:
        gk = Gatekeeper(make_cfg())
        fn = AsyncMock(return_value=42)
        resp = await gk.call(make_request(fn, target="cop_mcp"))
        assert resp.target == "cop_mcp"


# ---------------------------------------------------------------------------
# Retry behaviour
# ---------------------------------------------------------------------------


class TestGatekeeperRetry:
    @pytest.mark.asyncio
    async def test_retries_on_transient_failure(self) -> None:
        """Fails twice, succeeds on third attempt (max_retries=2 → 3 total)."""
        gk = Gatekeeper(make_cfg(retries=2))
        call_count = 0

        async def flaky() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # noqa: PLR2004
                msg = "transient"
                raise RuntimeError(msg)
            return "ok"

        resp = await gk.call(make_request(flaky))
        assert resp.result == "ok"
        assert resp.attempts == 3  # noqa: PLR2004
        assert call_count == 3  # noqa: PLR2004

    @pytest.mark.asyncio
    async def test_retries_exhausted_raises(self) -> None:
        """Fails on every attempt → GatekeeperRetryExhaustedError."""
        gk = Gatekeeper(make_cfg(retries=1))

        async def always_fail() -> None:
            msg = "boom"
            raise ValueError(msg)

        with pytest.raises(GatekeeperRetryExhaustedError):
            await gk.call(make_request(always_fail))
