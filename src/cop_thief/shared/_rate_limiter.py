"""Token-bucket rate limiter for the Gatekeeper.

Provides :class:`TokenBucket`, a simple async token-bucket that throttles
calls to a target without dropping them — callers are slowed down via
``asyncio.sleep`` until a token is available.

Traces: PLAN §8, T-P0-16.
"""

from __future__ import annotations

import asyncio
import time


class TokenBucket:
    """Simple token-bucket rate limiter (pure async sleep, no time-slicing).

    Args:
        rate: Refill rate in tokens per second.  The bucket starts full
            (``rate`` tokens) so the first burst is not penalised.

    """

    def __init__(self, rate: float) -> None:
        """Initialise the bucket at full capacity."""
        self._rate = rate           # tokens / second
        self._tokens = rate         # start full
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until a token is available, then consume one.

        The caller is suspended for exactly the time needed to refill one
        token if the bucket is empty; otherwise it returns immediately.
        """
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._tokens = min(self._rate, self._tokens + elapsed * self._rate)
            self._last_refill = now
            if self._tokens < 1:
                wait = (1 - self._tokens) / self._rate
                await asyncio.sleep(wait)
                self._tokens = 0.0
            else:
                self._tokens -= 1.0
