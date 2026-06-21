"""Exceptions and data-transfer types for the Gatekeeper.

Defines the error hierarchy (:class:`GatekeeperError` and subclasses)
and the :class:`OutboundRequest` / :class:`Response` dataclasses that
callers use when routing calls through :class:`~cop_thief.shared.gatekeeper.Gatekeeper`.

Traces: PLAN §8, NFR-5, T-P0-15.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class GatekeeperError(Exception):
    """Base class for all Gatekeeper errors."""


class GatekeeperRateLimitError(GatekeeperError):
    """Raised when a call is rejected due to a full queue (backpressure)."""


class GatekeeperTimeoutError(GatekeeperError):
    """Raised when a call exceeds the configured per-call timeout."""


class GatekeeperRetryExhaustedError(GatekeeperError):
    """Raised when all retry attempts have been exhausted."""


# ---------------------------------------------------------------------------
# Request / Response types
# ---------------------------------------------------------------------------


@dataclass
class OutboundRequest:
    """Descriptor for an outbound call routed through the Gatekeeper.

    Attributes:
        target: A logical target label (e.g. ``"cop_mcp"`` or ``"llm"``).
            Used for rate-limit bucketing and log correlation.
        fn: An *async* callable that performs the actual network call.
            It receives no arguments; capture state via closure.
        metadata: Arbitrary key/value pairs for logging (must not contain
            secrets — the :class:`RedactingFilter` is applied regardless).

    """

    target: str
    fn: Callable[[], Awaitable[Any]]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Response:
    """Wraps the result of an outbound call.

    Attributes:
        target: Echo of :attr:`OutboundRequest.target`.
        result: The value returned by :attr:`OutboundRequest.fn`.
        latency_s: Wall-clock seconds consumed by the call.
        attempts: Number of attempts made (1 = success on first try).

    """

    target: str
    result: Any
    latency_s: float
    attempts: int
