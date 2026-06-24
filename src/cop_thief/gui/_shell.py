"""Tkinter shell construction for the GUI app."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from cop_thief.gui.view_model import PALETTE


def build_shell(gui: object) -> None:
    """Attach canvas, controls, and transcript widgets to *gui*."""
    gui.canvas = tk.Canvas(  # type: ignore[attr-defined]
        gui.root,
        width=600,
        height=600,
        bg=PALETTE["bg"],
        highlightthickness=0,
    )
    gui.canvas.grid(row=0, column=0, rowspan=6, sticky="nsew", padx=16, pady=16)
    side = ttk.Frame(gui.root, padding=16)
    side.grid(row=0, column=1, sticky="nsew", padx=(0, 16), pady=16)
    ttk.Label(side, text="Cop-Thief Chase", font=("Segoe UI", 18, "bold")).pack(anchor="w")
    gui.score_label = ttk.Label(side, text="Cop 0 | Thief 0", font=("Segoe UI", 12))
    gui.score_label.pack(anchor="w", pady=(8, 12))
    _buttons(gui, side)
    ttk.Label(side, text="Replay speed").pack(anchor="w", pady=(10, 0))
    ttk.Scale(side, from_=120, to=1200, variable=gui.speed_ms, orient="horizontal").pack(fill="x")
    ttk.Label(side, textvariable=gui.status, wraplength=310).pack(anchor="w", pady=(12, 8))
    ttk.Label(side, text="NL transcript").pack(anchor="w")
    gui.message = tk.Text(side, height=8, width=42, wrap="word")
    gui.message.pack(fill="both", expand=True, pady=(6, 0))
    gui.root.columnconfigure(0, weight=1)
    gui.root.columnconfigure(1, weight=0)
    gui.root.rowconfigure(0, weight=1)


def _buttons(gui: object, side: ttk.Frame) -> None:
    buttons = ttk.Frame(side)
    buttons.pack(fill="x", pady=6)
    specs = [
        ("Run", gui.run_sub_game),
        ("Run Full", gui.run_full_game),
        ("Play", gui.play),
        ("Step", gui.step),
        ("Pause", gui.pause),
        ("Stop", gui.stop),
        ("Rewind", gui.rewind),
        ("Capture", gui.capture),
    ]
    for label, command in specs:
        ttk.Button(buttons, text=label, command=command).pack(side="left", padx=3)
