"""Final report dispatch orchestration."""

from __future__ import annotations

from typing import Protocol

from cop_thief.services.engine._lifecycle_types import FullGameResult
from cop_thief.services.report.builder import report_to_json
from cop_thief.services.report.emailer import GmailReportEmailer, ReportSendResult
from cop_thief.shared.config import Config
from cop_thief.shared.gatekeeper import Gatekeeper


class ReportSender(Protocol):
    """Protocol for report email senders."""

    async def send(self, json_body: str) -> ReportSendResult:
        """Send the already serialized report body."""
        ...


async def dispatch_final_report(
    config: Config,
    gatekeeper: Gatekeeper,
    result: FullGameResult,
    sender: ReportSender | None = None,
) -> tuple[str, ReportSendResult]:
    """Build, validate, and send the final JSON report."""
    body = report_to_json(config, result)
    emailer = sender or GmailReportEmailer(config, gatekeeper)
    send_result = await emailer.send(body)
    return body, send_result
