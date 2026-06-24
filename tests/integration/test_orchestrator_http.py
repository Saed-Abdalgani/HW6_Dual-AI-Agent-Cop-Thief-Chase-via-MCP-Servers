"""HTTP-localhost orchestrator integration coverage."""

from __future__ import annotations

import json
import socket
import textwrap
from pathlib import Path

import pytest

from cop_thief.sdk.facade import CopThiefSDK
from cop_thief.services.report.emailer import ReportSendResult
from cop_thief.shared.config import Config


async def _mock_llm(_prompt: str) -> str:
    return json.dumps({"action": "stay", "nl_message": "I'll wait here."})


class _FakeReportSender:
    async def send(self, json_body: str) -> ReportSendResult:  # noqa: ARG002
        return ReportSendResult(sent=True, message_id="fake-message")


def test_full_game_over_http_localhost_auto_launch(
    tmp_path: Path,
    minimal_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Full 6-game loop can run over live localhost HTTP MCP servers."""
    config_path = tmp_path / "http-config.yaml"
    config_path.write_text(_http_config(tmp_path, _free_port(), _free_port()), encoding="utf-8")
    monkeypatch.setenv("CONFIG_PATH", str(config_path))
    monkeypatch.setenv("MCP_STATE_PATH", str(tmp_path / "http-mcp-state.json"))

    sdk = CopThiefSDK(
        Config.from_env(),
        llm_caller=_mock_llm,
        report_sender=_FakeReportSender(),
    )
    report = sdk.run_full_game()

    assert report.sub_games_played == 6  # noqa: PLR2004
    assert len(report.result.sub_games) == 6  # noqa: PLR2004
    assert sdk._use_direct is False  # noqa: SLF001
    assert sdk._auto_launch is True  # noqa: SLF001


def _http_config(tmp_path: Path, cop_port: int, thief_port: int) -> str:
    return textwrap.dedent(
        f"""\
        grid_size: [5, 5]
        max_moves: 1
        num_games: 6
        max_barriers: 1
        scoring: {{ cop_win: 20, thief_win: 10, cop_loss: 5, thief_loss: 5 }}
        start_mode: random
        thief_moves_first: true
        discount_gamma: 0.95
        strategy: heuristic
        llm: {{ provider: openai, model: gpt-4o-mini, timeout_s: 30 }}
        mcp:
          mode: http
          auto_launch: true
          cop_url: "http://localhost:{cop_port}"
          thief_url: "http://localhost:{thief_port}"
        gatekeeper: {{ rate_limit_per_target: 100, max_retries: 1, queue_size: 64, timeout_s: 30 }}
        email: {{ to: "test@example.com" }}
        nlp: {{ tone: balanced, transcript_dir: "{(tmp_path / 'http-results').as_posix()}" }}
        timezone: "UTC"
        seed: 7
        """
    )


def _free_port() -> int:
    """Return an available localhost TCP port for a subprocess server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("localhost", 0))
        return int(sock.getsockname()[1])
