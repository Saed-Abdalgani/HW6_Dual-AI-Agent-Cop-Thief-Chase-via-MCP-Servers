"""Gatekeeper retry/timeout execution logic.

Factored out of :mod:`.gatekeeper` to keep each module under ~150 LOC.

Traces: NFR-5, T-P0-17, T-P0-19.
"""

from __future__ import annotations

import asyncio
import math
import random
import time
from typing import Any

from cop_thief.shared._gatekeeper_types import (
    GatekeeperRetryExhaustedError,
    GatekeeperTimeoutError,
    OutboundRequest,
    Response,
)
from cop_thief.shared.logging import get_logger

_log = get_logger(__name__)


async def execute_with_retries(
    request: OutboundRequest,
    max_retries: int,
    timeout_s: int,
) -> Response:
    """Execute *request.fn* with retries and per-call timeout.

    Args:
        request: The outbound request to run.
        max_retries: Maximum number of retry attempts (total = max_retries + 1).
        timeout_s: Per-call timeout in seconds.

    Returns:
        A :class:`Response` on success.

    Raises:
        GatekeeperTimeoutError: If a single attempt times out.
        GatekeeperRetryExhaustedError: If all attempts fail.

    """
    max_attempts = max_retries + 1
    start = time.monotonic()
    last_exc: BaseException | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            result = await _execute_once(request, timeout_s)
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
                wait = _backoff(attempt)
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


async def _execute_once(request: OutboundRequest, timeout_s: int) -> Any:
    """Execute *request.fn* with the configured per-call timeout."""
    try:
        return await asyncio.wait_for(request.fn(), timeout=float(timeout_s))
    except TimeoutError as exc:
        msg = f"Call to target '{request.target}' timed out after {timeout_s}s."
        raise GatekeeperTimeoutError(msg) from exc


def _backoff(attempt: int, base: float = 0.5, cap: float = 30.0) -> float:
    """Full-jitter exponential back-off.

    ``wait = random(0, min(cap, base * 2^attempt))``
    """
    ceiling = min(cap, base * math.pow(2, attempt))
    return random.uniform(0, ceiling)  # noqa: S311
