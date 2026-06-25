"""RedactingFilter and logger-redaction integration tests — T-P0-25 (part 2/2).

Covers:
- Bearer header tokens are scrubbed to [REDACTED].
- api_key=value patterns are scrubbed.
- token=value patterns are scrubbed.
- Explicitly registered literal patterns are scrubbed.
- Innocent text passes through unchanged.
- filter() always returns True (does not suppress records).
- Logger emitting a raw token does not expose it in caplog output.
"""

from __future__ import annotations

import logging

import pytest

from cop_thief.shared.auth import TokenStore
from cop_thief.shared.logging import RedactingFilter, get_logger


class TestRedactingFilter:
    def _make_record(self, message: str) -> logging.LogRecord:
        return logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=message,
            args=(),
            exc_info=None,
        )

    def test_bearer_token_redacted(self) -> None:
        filt = RedactingFilter()
        record = self._make_record("Authorization: Bearer sk-abc123xyz")
        filt.filter(record)
        assert "sk-abc123xyz" not in record.msg
        assert "[REDACTED]" in record.msg

    def test_api_key_value_redacted(self) -> None:
        filt = RedactingFilter()
        record = self._make_record("api_key=super-secret-value")
        filt.filter(record)
        assert "super-secret-value" not in record.msg

    def test_token_eq_value_redacted(self) -> None:
        filt = RedactingFilter()
        record = self._make_record("token='abc-def-ghi'")
        filt.filter(record)
        assert "abc-def-ghi" not in record.msg

    def test_registered_literal_redacted(self) -> None:
        filt = RedactingFilter()
        filt.register_pattern("my-secret-literal-token")
        record = self._make_record("Calling with my-secret-literal-token in URL")
        filt.filter(record)
        assert "my-secret-literal-token" not in record.msg
        assert "[REDACTED]" in record.msg

    def test_innocent_text_not_redacted(self) -> None:
        filt = RedactingFilter()
        record = self._make_record("Game started: cop at (2,3), thief at (0,0)")
        filt.filter(record)
        assert "Game started" in record.msg

    def test_filter_always_returns_true(self) -> None:
        filt = RedactingFilter()
        record = self._make_record("anything")
        assert filt.filter(record) is True


class TestLoggerRedaction:
    def test_logger_redacts_token_in_output(self, caplog: pytest.LogCaptureFixture) -> None:
        """Raw token must not appear in any log record."""
        store = TokenStore()
        raw_token = store.issue("cop")

        logger = get_logger("test.redaction_integration")
        with caplog.at_level(logging.INFO, logger="test.redaction_integration"):
            logger.info("Using token: Bearer %s", raw_token)

        for record in caplog.records:
            assert raw_token not in record.getMessage(), (
                f"Raw token found in log: {record.getMessage()}"
            )
