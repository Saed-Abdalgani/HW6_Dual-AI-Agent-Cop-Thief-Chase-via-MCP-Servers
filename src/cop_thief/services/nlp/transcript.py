"""JSONL transcript logging for natural-language MCP messages.

Traces: FR-NL4, T-P5-08.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from cop_thief.constants import Action, Agent


class TranscriptLogger:
    """Append per-turn natural-language messages to ``results/``."""

    def __init__(self, root: Path | str = "results") -> None:
        """Store the transcript output directory."""
        self._root = Path(root)
        self._path: Path | None = None
        self._sub_game_index = 0

    @property
    def path(self) -> Path | None:
        """Return the active transcript path, if a sub-game is running."""
        return self._path

    def start(self, sub_game_index: int) -> Path:
        """Open a fresh transcript for one sub-game."""
        self._root.mkdir(parents=True, exist_ok=True)
        self._sub_game_index = sub_game_index
        self._path = self._root / f"nl_transcript_subgame_{sub_game_index}.jsonl"
        self._path.write_text("", encoding="utf-8")
        return self._path

    def record(self, agent: Agent, action: Action, text: str, move_count: int) -> None:
        """Append one message exchange event."""
        if self._path is None:
            return
        event = {
            "ts": datetime.now(UTC).isoformat(),
            "sub_game_index": self._sub_game_index,
            "turn": move_count,
            "agent": agent.value,
            "action": action.value,
            "move_count": move_count,
            "text": text,
        }
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, sort_keys=True) + "\n")
