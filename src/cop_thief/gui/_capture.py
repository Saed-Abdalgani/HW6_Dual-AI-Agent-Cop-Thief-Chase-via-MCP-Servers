"""GUI capture helpers."""

from __future__ import annotations

from pathlib import Path


def save_board_capture(canvas: object) -> Path:
    """Save the current board canvas as PostScript evidence."""
    Path("assets").mkdir(exist_ok=True)
    target = Path("assets/gui_phase6_board.ps")
    canvas.postscript(file=str(target), colormode="color")  # type: ignore[attr-defined]
    return target
