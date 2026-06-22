"""Full end-to-end pipeline: 6 sub-games, NL, JSON report, schema validation."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from cop_thief.constants import Outcome
from cop_thief.mcp_servers import _state
from cop_thief.sdk.facade import CopThiefSDK
from cop_thief.services.report.builder import REPORT_KEYS, validate_report_json
from cop_thief.services.report.emailer import ReportSendResult
from cop_thief.shared.auth import default_store


@pytest.fixture()
def pipeline_config(tmp_path: Path, minimal_env: None, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fast config for a single comprehensive pipeline assertion."""
    cfg = textwrap.dedent(
        f"""\
        grid_size: [5, 5]
        max_moves: 2
        num_games: 6
        max_barriers: 1
        scoring:
          cop_win: 20
          thief_win: 10
          cop_loss: 5
          thief_loss: 5
        start_mode: random
        thief_moves_first: true
        discount_gamma: 0.95
        strategy: heuristic
        llm:
          provider: openai
          model: gpt-4o-mini
          timeout_s: 30
        mcp:
          cop_url: "http://localhost:8001"
          thief_url: "http://localhost:8002"
        gatekeeper:
          rate_limit_per_target: 100
          max_retries: 1
          queue_size: 64
          timeout_s: 30
        email:
          to: "test@example.com"
        nlp:
          tone: balanced
          transcript_dir: "{(tmp_path / 'results').as_posix()}"
        report:
          group_name: "Pipeline-Test"
          students: ["Tester"]
          github_repo: "https://github.com/example/marl-cop-thief"
        timezone: "UTC"
        seed: 7
        """
    )
    path = tmp_path / "config.yaml"
    path.write_text(cfg, encoding="utf-8")
    monkeypatch.setenv("CONFIG_PATH", str(path))
    monkeypatch.setattr(_state, "STATE_PATH", tmp_path / "mcp_state.json")
    default_store.register_token("cop", "test-cop-token")
    default_store.register_token("thief", "test-thief-token")
    return path


async def _mock_llm(prompt: str) -> str:
    return json.dumps({"action": "stay", "nl_message": "Watching the board carefully."})


class _CapturingSender:
    def __init__(self) -> None:
        self.body = ""

    async def send(self, json_body: str) -> ReportSendResult:
        self.body = json_body
        return ReportSendResult(sent=True, message_id="pipeline-msg")


def test_full_pipeline_six_games_nl_and_json_email(pipeline_config: Path) -> None:  # noqa: ARG001
    """Single test exercises SDK loop, NL transcripts, report JSON, and email dispatch."""
    from cop_thief.shared.config import Config

    config = Config.from_env()
    sender = _CapturingSender()
    sdk = CopThiefSDK(
        config,
        use_direct_mcp=True,
        llm_caller=_mock_llm,
        report_sender=sender,
    )
    report = sdk.run_full_game()

    assert report.sub_games_played == 6
    assert len(report.result.sub_games) == 6
    assert all(sg.moves_used <= config.max_moves for sg in report.result.sub_games)
    assert all(sg.barriers_used <= config.max_barriers for sg in report.result.sub_games)
    assert all(sg.winner in (Outcome.COP_WIN, Outcome.THIEF_WIN) for sg in report.result.sub_games)

    data = validate_report_json(report.report_json)
    assert set(data) == REPORT_KEYS
    assert len(data["sub_games"]) == 6
    assert data["totals"]["cop"] + data["totals"]["thief"] > 0
    assert sender.body == report.report_json
    assert report.email is not None and report.email.sent is True

    transcript_dir = Path(config.nlp.transcript_dir)
    transcripts = list(transcript_dir.glob("nl_transcript_subgame_*.jsonl"))
    assert len(transcripts) == 6
    for path in transcripts:
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        assert lines
        assert all("(2," not in line and "[2," not in line for line in lines)
