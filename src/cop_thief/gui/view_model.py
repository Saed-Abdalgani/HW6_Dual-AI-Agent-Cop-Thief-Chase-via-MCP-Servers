"""Pure GUI state mapping for the Cop–Thief board.

Traces: FR-G1, FR-G2, T-P6-02, T-P6-03, T-P6-05, T-P6-09.
"""

from __future__ import annotations

from dataclasses import dataclass

from cop_thief.sdk import GameState

PALETTE = {
    "bg": "#111827",
    "grid": "#243244",
    "empty": "#172033",
    "barrier": "#64748b",
    "cop": "#38bdf8",
    "thief": "#f97316",
    "both": "#facc15",
    "text": "#e5e7eb",
}


@dataclass(frozen=True)
class CellView:
    """Drawable cell information for one grid square."""

    row: int
    col: int
    x0: int
    y0: int
    x1: int
    y1: int
    fill: str
    label: str


@dataclass(frozen=True)
class BoardView:
    """Full board view-model consumed by Tkinter or tests."""

    cells: tuple[CellView, ...]
    status: str
    score: str
    message: str
    rows: int
    cols: int


def build_board_view(state: GameState, canvas_size: int = 560) -> BoardView:
    """Map SDK :class:`GameState` to fixed-size drawable cells."""
    rows, cols = state.grid_size
    pad = max(16, canvas_size // 28)
    cell = max(18, (canvas_size - pad * 2) // max(rows, cols))
    cells: list[CellView] = []
    barriers = set(state.barriers)
    for row in range(rows):
        for col in range(cols):
            pos = (row, col)
            fill, label = PALETTE["empty"], ""
            if pos in barriers:
                fill, label = PALETTE["barrier"], "B"
            if pos == state.cop_pos == state.thief_pos:
                fill, label = PALETTE["both"], "CT"
            elif pos == state.cop_pos:
                fill, label = PALETTE["cop"], "C"
            elif pos == state.thief_pos:
                fill, label = PALETTE["thief"], "T"
            x0, y0 = pad + col * cell, pad + row * cell
            cells.append(CellView(row, col, x0, y0, x0 + cell - 3, y0 + cell - 3, fill, label))
    return BoardView(
        cells=tuple(cells),
        status=_status_text(state),
        score=f"Cop {state.scores.get('cop', 0)} | Thief {state.scores.get('thief', 0)}",
        message=state.latest_message or "Waiting for the next message.",
        rows=rows,
        cols=cols,
    )


def _status_text(state: GameState) -> str:
    if state.over:
        winner = "Cop captured the thief" if state.winner == "cop_win" else "Thief escaped"
        return f"{winner} after {state.move_count} rounds"
    return f"Sub-game {state.sub_game_index or 1} | Round {state.move_count}"
