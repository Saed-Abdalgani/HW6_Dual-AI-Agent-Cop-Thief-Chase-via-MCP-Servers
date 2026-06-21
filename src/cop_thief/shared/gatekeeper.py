"""Central API Gatekeeper for all outbound calls.

Every external call — LLM, MCP HTTP, Gmail — **must** flow through
:class:`Gatekeeper`.  It enforces:

* **Rate limiting** — token-bucket per target URL (see :mod:`._rate_limiter`).
* **Retries** — exponential back-off with jitter (max attempts from config).
* **Bounded queue + backpressure** — rejects calls when the queue is full.
* **Per-call timeouts** — from config; raises :class:`GatekeeperTimeoutError`.
* **Structured logging with secret redaction** — no token/key ever in logs.

All parameters come from :class:`~cop_thief.shared.config.GatekeeperConfig`;
no values are hard-coded here.

Traces: PLAN §8, NFR-5, T-P0-15..T-P0-20.
"""

from __future__ import annotations

import asyncio
import math
import random
import time
from typing import Any

# Re-export so callers only need to import from this module.
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
        # Semaphore enforces the bounded queue / backpressure (T-P0-18).
        self._semaphore = asyncio.Semaphore(cfg.queue_size)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

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
        acquired = self._semaphore._value > 0  # noqa: SLF001 — peek without blocking
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
            return await self._execute_with_retries(request)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get_bucket(self, target: str) -> TokenBucket:
        """Return (or create) the rate-limit bucket for *target*."""
        if target not in self._buckets:
            self._buckets[target] = TokenBucket(self._cfg.rate_limit_per_target)
        return self._buckets[target]

    async def _execute_with_retries(self, request: OutboundRequest) -> Response:
        """Execute *request.fn* up to ``max_retries + 1`` times with backoff."""
        max_attempts = self._cfg.max_retries + 1
        start = time.monotonic()
        last_exc: BaseException | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                result = await self._execute_once(request)
                latency = time.monotonic() - start
                _log.info(
                    "Gatekeeper success: target=%s attempt=%d latency=%.3fs",
                    request.target, attempt, latency,
                )
                return Response(
                    target=request.target, result=result,
                    latency_s=latency, attempts=attempt,
                )
            except GatekeeperTimeoutError:
                raise
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if attempt < max_attempts:
                    wait = self._backoff(attempt)
                    _log.warning(
                        "Gatekeeper transient failure: target=%s attempt=%d/%d "
                        "error=%r wait=%.3fs",
                        request.target, attempt, max_attempts, str(exc), wait,
                    )
                    await asyncio.sleep(wait)

        latency = time.monotonic() - start
        _log.error(
            "Gatekeeper retries exhausted: target=%s attempts=%d latency=%.3fs",
            request.target, max_attempts, latency,
        )
        msg = (
            f"All {max_attempts} attempt(s) failed for target '{request.target}'. "
            f"Last error: {last_exc!r}"
        )
        raise GatekeeperRetryExhaustedError(msg) from last_exc

    async def _execute_once(self, request: OutboundRequest) -> Any:
        """Execute *request.fn* with the configured per-call timeout."""
        try:
            return await asyncio.wait_for(
                request.fn(), timeout=float(self._cfg.timeout_s),
            )
        except TimeoutError as exc:
            msg = (
                f"Call to target '{request.target}' timed out "
                f"after {self._cfg.timeout_s}s."
            )
            raise GatekeeperTimeoutError(msg) from exc

    @staticmethod
    def _backoff(attempt: int, base: float = 0.5, cap: float = 30.0) -> float:
        """Full-jitter exponential back-off (T-P0-17).

        ``wait = random(0, min(cap, base * 2^attempt))``
        """
        ceiling = min(cap, base * math.pow(2, attempt))
        return random.uniform(0, ceiling)  # noqa: S311 — not security-sensitive
