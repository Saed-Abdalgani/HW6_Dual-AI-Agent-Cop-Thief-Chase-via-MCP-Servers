"""Transcript panel rendering helpers."""

from __future__ import annotations


def render_transcript(widget: object, lines: list[str], message: str) -> None:
    """Append a non-duplicate message and redraw the transcript widget."""
    if (
        message
        and message != "Waiting for the next message."
        and (not lines or lines[-1] != message)
    ):
        lines.append(message)
    widget.delete("1.0", "end")  # type: ignore[attr-defined]
    widget.insert("1.0", "\n".join(lines[-80:]))  # type: ignore[attr-defined]
