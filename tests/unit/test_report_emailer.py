"""Unit tests for Gmail report emailer."""

from __future__ import annotations

from typing import Any

import pytest

from cop_thief.services.report.emailer import (
    GmailReportEmailer,
    build_gmail_raw_message,
    build_smtp_message,
    extract_mime_body,
)
from cop_thief.shared.config import Config
from cop_thief.shared.gatekeeper import Gatekeeper


def test_gmail_raw_message_body_is_json_only() -> None:
    body = '{"hello":"world"}'
    raw = build_gmail_raw_message("test@example.com", body)
    assert extract_mime_body(raw) == body


def test_smtp_message_body_is_json_only() -> None:
    body = '{"hello":"smtp"}'
    raw = build_smtp_message("from@example.com", "to@example.com", body)
    assert raw.split("\r\n\r\n", 1)[1] == body


@pytest.mark.asyncio
async def test_gmail_emailer_sends_with_gatekeeper(
    valid_config_yaml: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = Config.from_yaml(str(valid_config_yaml))
    monkeypatch.setenv("GMAIL_ACCESS_TOKEN", "token")
    seen: dict[str, Any] = {}

    async def poster(url: str, headers: dict[str, str], payload: dict[str, str]) -> dict[str, Any]:
        seen.update({"url": url, "headers": headers, "body": extract_mime_body(payload["raw"])})
        return {"id": "gmail-id"}

    emailer = GmailReportEmailer(cfg, Gatekeeper(cfg.gatekeeper), poster=poster)
    result = await emailer.send('{"ok":true}')
    assert result.sent is True
    assert result.message_id == "gmail-id"
    assert seen["headers"]["Authorization"] == "Bearer token"
    assert seen["body"] == '{"ok":true}'


@pytest.mark.asyncio
async def test_gmail_emailer_skips_without_access_token(valid_config_yaml: object) -> None:
    cfg = Config.from_yaml(str(valid_config_yaml))
    emailer = GmailReportEmailer(cfg, Gatekeeper(cfg.gatekeeper))
    result = await emailer.send('{"ok":true}')
    assert result.sent is False
    assert result.skipped is True


@pytest.mark.asyncio
async def test_gmail_emailer_sends_with_app_password(
    valid_config_yaml: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = Config.from_yaml(str(valid_config_yaml))
    monkeypatch.delenv("GMAIL_ACCESS_TOKEN", raising=False)
    monkeypatch.setenv("GMAIL_USER", "sender@example.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "app-pass")
    seen: dict[str, str] = {}

    async def smtp_sender(
        user: str,
        password: str,
        to_addr: str,
        message: str,
        json_body: str,
    ) -> str:
        seen.update(
            {
                "user": user,
                "password": password,
                "to": to_addr,
                "message": message,
                "body": json_body,
            }
        )
        return "smtp-id"

    emailer = GmailReportEmailer(cfg, Gatekeeper(cfg.gatekeeper), smtp_sender=smtp_sender)
    result = await emailer.send('{"ok":true}')
    assert result.sent is True
    assert result.message_id == "smtp-id"
    assert seen["body"] == '{"ok":true}'
    assert seen["message"].split("\r\n\r\n", 1)[1] == '{"ok":true}'
