"""Unit tests for Phase P6 GUI view-model mapping."""

from __future__ import annotations

from cop_thief.gui.view_model import PALETTE, build_board_view
from cop_thief.sdk import GameState


def test_build_board_view_uses_configured_grid_size() -> None:
    state = GameState(grid_size=(7, 5), cop_pos=(0, 0), thief_pos=(6, 4))
    view = build_board_view(state, canvas_size=350)
    assert view.rows == 7
    assert view.cols == 5
    assert len(view.cells) == 35


def test_build_board_view_idle_state_hides_default_agents() -> None:
    state = GameState(grid_size=(5, 5), idle=True)
    view = build_board_view(state)
    assert "Press Run" in view.status
    assert all(cell.label == "" for cell in view.cells)


def test_build_board_view_marks_agents_and_barriers() -> None:
    state = GameState(
        grid_size=(5, 5),
        cop_pos=(1, 1),
        thief_pos=(3, 3),
        barriers=[(2, 2)],
    )
    view = build_board_view(state)
    labels = {(cell.row, cell.col): cell.label for cell in view.cells if cell.label}
    assert labels[(1, 1)] == "C"
    assert labels[(3, 3)] == "T"
    assert labels[(2, 2)] == "B"


def test_build_board_view_marks_capture_cell() -> None:
    state = GameState(grid_size=(5, 5), cop_pos=(2, 2), thief_pos=(2, 2))
    cell = next(c for c in build_board_view(state).cells if (c.row, c.col) == (2, 2))
    assert cell.label == "CT"
    assert cell.fill == PALETTE["both"]


def test_build_board_view_marks_cop_on_barrier_cell() -> None:
    state = GameState(grid_size=(5, 5), cop_pos=(2, 2), thief_pos=(4, 4), barriers=[(2, 2)])
    cell = next(c for c in build_board_view(state).cells if (c.row, c.col) == (2, 2))
    assert cell.label == "C+B"
    assert cell.fill == PALETTE["cop"]


def test_build_board_view_status_score_and_message() -> None:
    state = GameState(
        over=True,
        winner="cop_win",
        move_count=4,
        scores={"cop": 20, "thief": 5},
        latest_message="I am pressing toward the east side.",
    )
    view = build_board_view(state)
    assert "Cop captured" in view.status
    assert "Barriers 0/5" in view.status
    assert view.score == "Cop 20 | Thief 5"
    assert "east" in view.message


def test_gui_app_imports_without_launching() -> None:
    from cop_thief.gui.app import CopThiefGui, main

    assert CopThiefGui.__name__ == "CopThiefGui"
    assert callable(main)
