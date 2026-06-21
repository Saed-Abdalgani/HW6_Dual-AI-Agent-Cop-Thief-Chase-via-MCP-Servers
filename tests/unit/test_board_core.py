"""Unit tests for core Board class functionality.

Covers construction, dimension validation, in-bounds detection, and barrier storage.
Traces: T-P1-20, T-P1-03, T-P1-04, FR-B1, FR-B2, FR-BR3, FR-M3.
"""

from __future__ import annotations

import pytest

from cop_thief.services.engine.board import Board


def test_board_default_5x5() -> None:
    """Board accepts a 5×5 grid."""
    b = Board(rows=5, cols=5)
    assert b.rows == 5
    assert b.cols == 5


def test_board_arbitrary_7x7() -> None:
    """Board accepts a 7×7 grid."""
    b = Board(rows=7, cols=7)
    assert b.rows == 7 and b.cols == 7


def test_board_rejects_tiny_grid() -> None:
    """Board raises ValueError when dimensions are less than 2."""
    with pytest.raises(ValueError, match="2×2"):
        Board(rows=1, cols=5)


def test_in_bounds_center() -> None:
    """Center cell is in-bounds."""
    b = Board(rows=5, cols=5)
    assert b.in_bounds((2, 2)) is True


def test_in_bounds_corners() -> None:
    """All four corners are in-bounds."""
    b = Board(rows=5, cols=5)
    for pos in [(0, 0), (0, 4), (4, 0), (4, 4)]:
        assert b.in_bounds(pos) is True


def test_out_of_bounds_negative_row() -> None:
    """Negative row is out-of-bounds."""
    b = Board(rows=5, cols=5)
    assert b.in_bounds((-1, 2)) is False


def test_out_of_bounds_col_too_large() -> None:
    """Column >= cols is out-of-bounds."""
    b = Board(rows=5, cols=5)
    assert b.in_bounds((2, 5)) is False


def test_out_of_bounds_both() -> None:
    """Both row and col out-of-bounds."""
    b = Board(rows=5, cols=5)
    assert b.in_bounds((10, 10)) is False


def test_is_blocked_empty_board() -> None:
    """No barriers initially."""
    b = Board(rows=5, cols=5)
    assert b.is_blocked((2, 2)) is False


def test_place_barrier_marks_cell() -> None:
    """place_barrier makes the cell blocked."""
    b = Board(rows=5, cols=5)
    b.place_barrier((3, 3))
    assert b.is_blocked((3, 3)) is True


def test_place_barrier_increments_counter() -> None:
    """Barrier counter increments per placement."""
    b = Board(rows=5, cols=5)
    b.place_barrier((1, 1))
    b.place_barrier((2, 2))
    assert b.barriers_used == 2


def test_barrier_does_not_block_other_cells() -> None:
    """Placing a barrier at one cell doesn't block adjacent cells."""
    b = Board(rows=5, cols=5)
    b.place_barrier((2, 2))
    assert b.is_blocked((2, 3)) is False
    assert b.is_blocked((3, 2)) is False


def test_is_legal_cell_blocked() -> None:
    """is_legal_cell returns False for a barrier cell."""
    b = Board(rows=5, cols=5)
    b.place_barrier((0, 0))
    assert b.is_legal_cell((0, 0)) is False


def test_is_legal_cell_in_bounds_free() -> None:
    """is_legal_cell returns True for an in-bounds free cell."""
    b = Board(rows=5, cols=5)
    assert b.is_legal_cell((2, 2)) is True


def test_is_legal_cell_out_of_bounds() -> None:
    """is_legal_cell returns False for an out-of-bounds cell."""
    b = Board(rows=5, cols=5)
    assert b.is_legal_cell((-1, 0)) is False
