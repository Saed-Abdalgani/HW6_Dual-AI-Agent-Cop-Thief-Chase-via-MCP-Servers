"""Structured logger factory for the Cop–Thief MCP system.

All modules obtain their logger via :func:`get_logger` rather than calling
``logging.getLogger`` directly.  The factory installs a :class:`RedactingFilter`
that scrubs known secret patterns before any record reaches a handler, so tokens
and API keys can **never** appear in logs.

Traces: NFR-10, T-P0-20, T-P0-21, CC-LOG, CC-SEC.
"""

from __future__ import annotations

import logging
import re
from typing import ClassVar

# ---------------------------------------------------------------------------
# Secret redaction filter
# ---------------------------------------------------------------------------

_SECRET_PATTERN = re.compile(
    r"""(
        (?:Bearer\s+)[^\s"']+       # Authorization headers
        | (?:key|token|secret|password|credential|api_key)
          \s*[=:]\s*["']?[^\s"',>]+  # key=value style
    )""",
    re.IGNORECASE | re.VERBOSE,
)

_REDACTED = "[REDACTED]"


class RedactingFilter(logging.Filter):
    """A :class:`logging.Filter` that replaces secret-like strings with ``[REDACTED]``.

    Applied to every logger created by :func:`get_logger` so that no handler
    (console, file, remote) ever receives plaintext credentials.
    """

    _EXTRA_PATTERNS: ClassVar[list[re.Pattern[str]]] = []

    @classmethod
    def register_pattern(cls, pattern: str | re.Pattern[str]) -> None:
        """Register an additional redaction pattern at runtime.

        Useful when a secret value is known at startup (e.g. after loading
        a token from the environment) and should be completely masked.

        Args:
            pattern: A string literal or compiled regex to redact.

        """
        if isinstance(pattern, str):
            pattern = re.compile(re.escape(pattern))
        cls._EXTRA_PATTERNS.append(pattern)

    def filter(self, record: logging.LogRecord) -> bool:
        """Scrub the log message in-place; always returns ``True``."""
        record.msg = self._scrub(str(record.msg))
        record.args = self._scrub_args(record.args)
        return True

    @classmethod
    def _scrub(cls, text: str) -> str:
        text = _SECRET_PATTERN.sub(_REDACTED, text)
        for pat in cls._EXTRA_PATTERNS:
            text = pat.sub(_REDACTED, text)
        return text

    @classmethod
    def _scrub_args(cls, args: object) -> object:
        if isinstance(args, tuple):
            return tuple(cls._scrub(str(a)) if isinstance(a, str) else a for a in args)
        if isinstance(args, dict):
            return {k: (cls._scrub(str(v)) if isinstance(v, str) else v) for k, v in args.items()}
        return args


# ---------------------------------------------------------------------------
# Logger factory
# ---------------------------------------------------------------------------

_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"
_redacting_filter = RedactingFilter()


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Return a named, redaction-aware :class:`logging.Logger`.

    If the logger already exists (cached by the logging machinery), the
    existing instance is returned so that configuration is applied only once.

    Args:
        name: Typically ``__name__`` of the calling module.
        level: Logging level (default :data:`logging.INFO`).

    Returns:
        A :class:`logging.Logger` instance with a :class:`RedactingFilter`
        and a ``StreamHandler`` attached.

    """
    logger = logging.getLogger(name)
    if logger.handlers:
        # Already configured — return early.
        return logger

    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATE_FORMAT))
    handler.addFilter(_redacting_filter)
    logger.addFilter(_redacting_filter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger
