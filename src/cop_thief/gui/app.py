"""Tkinter GUI for the Cop–Thief chase.

The GUI consumes the SDK only; it does not import engine or orchestrator modules.
Traces: FR-G1..3, NFR-7, T-P6-01..08.
"""

from __future__ import annotations

import threading
import tkinter as tk

from cop_thief.gui._capture import save_board_capture
from cop_thief.gui._shell import build_shell
from cop_thief.gui._transcript_panel import render_transcript
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
        self.stopped = False
        self.transcript_lines: list[str] = []
        self.status = tk.StringVar(value="Ready")
        self.speed_ms = tk.IntVar(value=420)
        self.root.title("Cop-Thief Chase")
        self.root.configure(bg=PALETTE["bg"])
        build_shell(self)
        self._draw(self.frames[0])

    def run_sub_game(self) -> None:
        """Run one autonomous sub-game off the UI thread."""
        self.status.set("Running autonomous sub-game...")
        self._reset_live_run()
        threading.Thread(target=self._run_worker, args=(False,), daemon=True).start()

    def run_full_game(self) -> None:
        """Run all configured sub-games off the UI thread."""
        self.status.set("Running full autonomous game...")
        self._reset_live_run()
        threading.Thread(target=self._run_worker, args=(True,), daemon=True).start()

    def _reset_live_run(self) -> None:
        self.playing = False
        self.stopped = False
        self.frames = []
        self.frame_idx = 0
        self.transcript_lines = []

    def _run_worker(self, full_game: bool) -> None:
        try:
            result = (
                self.sdk.run_full_game(on_frame=self._threadsafe_frame)
                if full_game
                else self.sdk.run_sub_game(on_frame=self._threadsafe_frame)
            )
            if not self.frames:
                self.frames = self.sdk.get_replay_frames() or [self.sdk.get_state()]
            winner = getattr(getattr(result, "winner", None), "value", None)
            text = f"Loaded {len(self.frames)} frames."
            if winner:
                text = f"{text} Winner: {winner}."
            self.root.after(0, lambda: self._ready(text))
        except Exception as exc:  # noqa: BLE001
            text = f"Run failed: {exc}"
            self.root.after(0, lambda: self.status.set(text))

    def _threadsafe_frame(self, frame: object) -> None:
        if not self.stopped:
            self.root.after(0, lambda: self._append_live_frame(frame))

    def _append_live_frame(self, frame: object) -> None:
        self.frames.append(frame)  # type: ignore[arg-type]
        self.frame_idx = len(self.frames) - 1
        self._draw(frame)

    def _ready(self, text: str) -> None:
        self.frame_idx = max(0, len(self.frames) - 1)
        self.status.set(text)
        if self.frames:
            self._draw(self.frames[self.frame_idx])

    def play(self) -> None:
        """Animate the loaded replay frames."""
        self.playing = True
        self._tick()

    def pause(self) -> None:
        """Pause replay animation."""
        self.playing = False

    def stop(self) -> None:
        """Stop live updates and replay animation."""
        self.stopped = True
        self.playing = False
        self.status.set("Stopped")

    def rewind(self) -> None:
        """Return replay to frame zero."""
        self.playing = False
        self.frame_idx = 0
        if self.frames:
            self._draw(self.frames[0])

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
            self.root.after(int(self.speed_ms.get()), self._tick)

    def _advance_frame(self) -> None:
        self.frame_idx = min(self.frame_idx + 1, len(self.frames) - 1)
        self._draw(self.frames[self.frame_idx])

    def _draw(self, state: object) -> None:
        view = build_board_view(state)  # type: ignore[arg-type]
        draw_board(self.canvas, view)
        self.score_label.configure(text=view.score)
        self.status.set(view.status)
        render_transcript(self.message, self.transcript_lines, view.message)

    def capture(self) -> None:
        """Save a PostScript board capture into assets for evidence."""
        target = save_board_capture(self.canvas)
        self.status.set(f"Captured {target}")


def main() -> None:
    """Launch the Tkinter GUI."""
    root = tk.Tk()
    CopThiefGui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
