"""Tkinter canvas drawing helpers for the GUI."""

from __future__ import annotations

import tkinter as tk

from cop_thief.gui.view_model import PALETTE, BoardView


def draw_board(canvas: tk.Canvas, view: BoardView) -> None:
    """Render a board view-model onto a Tkinter canvas."""
    canvas.delete("all")
    canvas.create_text(
        26,
        16,
        anchor="nw",
        fill=PALETTE["text"],
        text=f"{view.rows} x {view.cols}",
    )
    for cell in view.cells:
        canvas.create_rectangle(
            cell.x0,
            cell.y0,
            cell.x1,
            cell.y1,
            fill=cell.fill,
            outline=PALETTE["grid"],
        )
        if cell.label:
            cx, cy = (cell.x0 + cell.x1) // 2, (cell.y0 + cell.y1) // 2
            canvas.create_text(
                cx,
                cy,
                fill="#0f172a",
                text=cell.label,
                font=("Segoe UI", 14, "bold"),
            )
