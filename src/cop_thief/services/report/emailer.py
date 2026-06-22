"""Gmail API sender for JSON-only reports.

Traces: FR-E1..4, NFR-5, T-P8-05..08.
"""

from __future__ import annotations

import base64
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import httpx

from cop_thief.shared._gatekeeper_types import OutboundRequest
from cop_thief.shared.config import Config
from cop_thief.shared.gatekeeper import Gatekeeper

GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
HttpPoster = Callable[[str, dict[str, str], dict[str, str]], Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class ReportSendResult:
    """Outcome of a report email attempt."""

    sent: bool
    skipped: bool = False
    message_id: str = ""
    error: str = ""


class GmailReportEmailer:
    """Send final reports through Gmail API behind the Gatekeeper."""

    def __init__(
        self,
        config: Config,
        gatekeeper: Gatekeeper,
        poster: HttpPoster | None = None,
    ) -> None:
        """Wire config, Gatekeeper, and optional test poster."""
        self._cfg = config
        self._gk = gatekeeper
        self._poster = poster or _post_json

    async def send(self, json_body: str) -> ReportSendResult:
        """Send *json_body* as the exact email body."""
        token = Config.load_secret("GMAIL_ACCESS_TOKEN", required=False)
        if not token:
            return ReportSendResult(False, skipped=True, error="GMAIL_ACCESS_TOKEN not set.")
        raw = build_gmail_raw_message(self._cfg.email.to, json_body)
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        async def _fn() -> dict[str, Any]:
            return await self._poster(GMAIL_SEND_URL, headers, {"raw": raw})

        try:
            response = await self._gk.call(OutboundRequest(target="gmail", fn=_fn))
        except Exception as exc:  # noqa: BLE001
            return ReportSendResult(False, error=str(exc))
        return ReportSendResult(True, message_id=str(response.result.get("id", "")))


def build_gmail_raw_message(to_addr: str, json_body: str) -> str:
    """Return base64url MIME where the decoded body is exactly *json_body*."""
    mime = "\r\n".join(
        [
            f"To: {to_addr}",
            "Subject: Cop-Thief JSON Report",
            "Content-Type: application/json; charset=utf-8",
            "",
            json_body,
        ],
    )
    return base64.urlsafe_b64encode(mime.encode("utf-8")).decode("ascii")


def extract_mime_body(raw: str) -> str:
    """Decode a raw Gmail message and return the body section."""
    decoded = base64.urlsafe_b64decode(raw.encode("ascii")).decode("utf-8")
    return decoded.split("\r\n\r\n", 1)[1]


async def _post_json(url: str, headers: dict[str, str], payload: dict[str, str]) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, dict) else {"result": data}
