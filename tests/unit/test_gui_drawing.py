"""Unit tests for GUI drawing helpers."""

from __future__ import annotations

from cop_thief.gui.drawing import draw_board
from cop_thief.gui.view_model import build_board_view
from cop_thief.sdk import GameState


class FakeCanvas:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def delete(self, *args) -> None:
        self.calls.append("delete")

    def create_text(self, *args, **kwargs) -> None:
        self.calls.append("text")

    def create_rectangle(self, *args, **kwargs) -> None:
        self.calls.append("rect")


def test_draw_board_draws_grid_and_labels() -> None:
    canvas = FakeCanvas()
    state = GameState(grid_size=(2, 2), cop_pos=(0, 0), thief_pos=(1, 1), barriers=[(0, 1)])
    draw_board(canvas, build_board_view(state))
    assert canvas.calls.count("rect") == 4
    assert canvas.calls.count("text") >= 4
