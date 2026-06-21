"""Central API Gatekeeper for all outbound calls.

Every external call — LLM, MCP HTTP, Gmail — **must** flow through
:class:`Gatekeeper`. It enforces rate limiting, backpressure, retries,
timeouts, and structured logging with secret redaction.

Retry and timeout logic lives in :mod:`._gatekeeper_executor`.

Traces: PLAN §8, NFR-5, T-P0-15..T-P0-20.
"""

from __future__ import annotations

import asyncio

# Re-export so callers only need to import from this module.
from cop_thief.shared._gatekeeper_executor import execute_with_retries
from cop_thief.shared._gatekeeper_types import (  # noqa: F401
    GatekeeperError,
    GatekeeperRateLimitError,
    GatekeeperRetryExhaustedError,
    GatekeeperTimeoutError,
    OutboundRequest,
    Response,
)
from cop_thief.shared._rate_limiter import TokenBucket
from cop_thief.shared.config import GatekeeperConfig
from cop_thief.shared.logging import get_logger

__all__ = [
    "Gatekeeper",
    "GatekeeperError",
    "GatekeeperRateLimitError",
    "GatekeeperRetryExhaustedError",
    "GatekeeperTimeoutError",
    "OutboundRequest",
    "Response",
]

_log = get_logger(__name__)


class Gatekeeper:
    """Central clearinghouse for all external calls.

    Instantiate once with a :class:`~cop_thief.shared.config.GatekeeperConfig`
    and call :meth:`call` for every outbound request.

    Args:
        cfg: Gatekeeper configuration section from the main config.

    """

    def __init__(self, cfg: GatekeeperConfig) -> None:
        """Initialize the Gatekeeper with the given configuration."""
        self._cfg = cfg
        self._buckets: dict[str, TokenBucket] = {}
        self._semaphore = asyncio.Semaphore(cfg.queue_size)

    async def call(self, request: OutboundRequest) -> Response:
        """Route *request* through rate-limiting, queueing, retries, and timeout.

        Args:
            request: The :class:`OutboundRequest` to execute.

        Returns:
            A :class:`Response` with the result and telemetry.

        Raises:
            GatekeeperRateLimitError: When the bounded queue is full.
            GatekeeperRetryExhaustedError: When all retry attempts fail.
            GatekeeperTimeoutError: When a single attempt exceeds the timeout.

        """
        acquired = self._semaphore._value > 0  # noqa: SLF001
        if not acquired:
            _log.warning(
                "Gatekeeper queue saturated for target=%s; rejecting request.",
                request.target,
            )
            msg = f"Queue saturated for target '{request.target}'. Try again later."
            raise GatekeeperRateLimitError(msg)

        async with self._semaphore:
            bucket = self._get_bucket(request.target)
            await bucket.acquire()
            return await execute_with_retries(
                request,
                max_retries=self._cfg.max_retries,
                timeout_s=self._cfg.timeout_s,
            )

    def _get_bucket(self, target: str) -> TokenBucket:
        """Return (or create) the rate-limit bucket for *target*."""
        if target not in self._buckets:
            self._buckets[target] = TokenBucket(self._cfg.rate_limit_per_target)
        return self._buckets[target]
