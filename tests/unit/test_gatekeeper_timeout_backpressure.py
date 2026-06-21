"""Gatekeeper timeout and backpressure tests — T-P0-24 (part 2/2).

Covers:
- Slow call raises GatekeeperTimeoutError.
- Timeout is NOT retried (only one attempt made).
- Saturated queue rejects the second call immediately with GatekeeperRateLimitError.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest

from cop_thief.shared.config import GatekeeperConfig
from cop_thief.shared.gatekeeper import (
    Gatekeeper,
    GatekeeperRateLimitError,
    GatekeeperTimeoutError,
    OutboundRequest,
)

# ---------------------------------------------------------------------------
# Helpers (duplicated from test_gatekeeper_success_retry for module isolation)
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
# Timeout
# ---------------------------------------------------------------------------


class TestGatekeeperTimeout:
    @pytest.mark.asyncio
    async def test_slow_call_raises_timeout(self) -> None:
        gk = Gatekeeper(make_cfg(timeout=1))

        async def slow() -> None:
            await asyncio.sleep(10)

        with pytest.raises(GatekeeperTimeoutError):
            await gk.call(make_request(slow))

    @pytest.mark.asyncio
    async def test_timeout_not_retried(self) -> None:
        """Timeout must propagate immediately — never retried."""
        gk = Gatekeeper(make_cfg(timeout=1, retries=5))
        call_count = 0

        async def slow() -> None:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(10)

        with pytest.raises(GatekeeperTimeoutError):
            await gk.call(make_request(slow))
        assert call_count == 1  # only one attempt


# ---------------------------------------------------------------------------
# Backpressure / queue saturation
# ---------------------------------------------------------------------------


class TestGatekeeperBackpressure:
    @pytest.mark.asyncio
    async def test_saturated_queue_raises_rate_limit_error(self) -> None:
        """A queue of size 1 already occupied must reject the next call."""
        gk = Gatekeeper(make_cfg(queue=1))

        async def hold() -> str:
            await asyncio.sleep(0.5)
            return "done"

        # First call grabs the only semaphore slot.
        task = asyncio.create_task(gk.call(make_request(hold)))
        # Yield so the task can acquire the semaphore.
        await asyncio.sleep(0)

        with pytest.raises(GatekeeperRateLimitError):
            await gk.call(make_request(AsyncMock(return_value="x")))

        await task  # clean up
