"""Tkinter GUI for the Cop–Thief chase.

The GUI consumes the SDK only; it does not import engine or orchestrator modules.
Traces: FR-G1..3, NFR-7, T-P6-01..08.
"""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from cop_thief.gui.drawing import draw_board
from cop_thief.gui.view_model import PALETTE, build_board_view
from cop_thief.sdk import CopThiefSDK


class CopThiefGui:
    """Interactive board, replay controls, scores, and NL transcript panel."""

    def __init__(self, root: tk.Tk, sdk: CopThiefSDK | None = None) -> None:
        """Build the GUI around a SDK instance."""
        self.root = root
        self.sdk = sdk or CopThiefSDK.from_env()
        self.frames = [self.sdk.get_state()]
        self.frame_idx = 0
        self.playing = False
        self.status = tk.StringVar(value="Ready")
        self.root.title("Cop-Thief Chase")
        self.root.configure(bg=PALETTE["bg"])
        self._build_shell()
        self._draw(self.frames[0])

    def _build_shell(self) -> None:
        self.canvas = tk.Canvas(
            self.root,
            width=600,
            height=600,
            bg=PALETTE["bg"],
            highlightthickness=0,
        )
        self.canvas.grid(row=0, column=0, rowspan=6, sticky="nsew", padx=16, pady=16)
        side = ttk.Frame(self.root, padding=16)
        side.grid(row=0, column=1, sticky="nsew", padx=(0, 16), pady=16)
        ttk.Label(side, text="Cop-Thief Chase", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        self.score_label = ttk.Label(side, text="Cop 0 | Thief 0", font=("Segoe UI", 12))
        self.score_label.pack(anchor="w", pady=(8, 12))
        buttons = ttk.Frame(side)
        buttons.pack(fill="x", pady=6)
        ttk.Button(buttons, text="Run", command=self.run_sub_game).pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text="Play", command=self.play).pack(side="left", padx=6)
        ttk.Button(buttons, text="Step", command=self.step).pack(side="left", padx=6)
        ttk.Button(buttons, text="Capture", command=self.capture).pack(side="left", padx=6)
        ttk.Label(side, textvariable=self.status, wraplength=310).pack(anchor="w", pady=(12, 8))
        ttk.Label(side, text="Latest NL message").pack(anchor="w")
        self.message = tk.Text(side, height=8, width=42, wrap="word")
        self.message.pack(fill="both", expand=True, pady=(6, 0))
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=0)
        self.root.rowconfigure(0, weight=1)

    def run_sub_game(self) -> None:
        """Run one autonomous sub-game off the UI thread."""
        self.status.set("Running autonomous sub-game...")
        threading.Thread(target=self._run_worker, daemon=True).start()

    def _run_worker(self) -> None:
        try:
            result = self.sdk.run_sub_game()
            self.frames = self.sdk.get_replay_frames() or [self.sdk.get_state()]
            text = f"Loaded {len(self.frames)} frames. Winner: {result.winner.value}."
            self.root.after(0, lambda: self._ready(text))
        except Exception as exc:  # noqa: BLE001
            text = f"Run failed: {exc}"
            self.root.after(0, lambda: self.status.set(text))

    def _ready(self, text: str) -> None:
        self.frame_idx = 0
        self.status.set(text)
        self._draw(self.frames[0])

    def play(self) -> None:
        """Animate the loaded replay frames."""
        self.playing = True
        self._tick()

    def step(self) -> None:
        """Advance one replay frame."""
        self.playing = False
        self._advance_frame()

    def _tick(self) -> None:
        if not self.playing:
            return
        self._advance_frame()
        self.playing = self.frame_idx < len(self.frames) - 1
        if self.playing:
            self.root.after(420, self._tick)

    def _advance_frame(self) -> None:
        self.frame_idx = min(self.frame_idx + 1, len(self.frames) - 1)
        self._draw(self.frames[self.frame_idx])

    def _draw(self, state: object) -> None:
        view = build_board_view(state)  # type: ignore[arg-type]
        draw_board(self.canvas, view)
        self.score_label.configure(text=view.score)
        self.status.set(view.status)
        self.message.delete("1.0", "end")
        self.message.insert("1.0", view.message)

    def capture(self) -> None:
        """Save a PostScript board capture into assets for evidence."""
        Path("assets").mkdir(exist_ok=True)
        target = Path("assets/gui_phase6_board.ps")
        self.canvas.postscript(file=str(target), colormode="color")
        self.status.set(f"Captured {target}")


def main() -> None:
    """Launch the Tkinter GUI."""
    root = tk.Tk()
    CopThiefGui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
