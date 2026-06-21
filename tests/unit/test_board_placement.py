"""Unit tests for Board agent placement and reset functionality.

Covers position getters/setters, random and strategy start-position generation,
reset behavior, and deterministic seeding.
Traces: T-P1-20, T-P1-05, NFR-11, FR-B3, FR-B4.
"""

from __future__ import annotations

import random

from cop_thief.constants import Agent, StartMode
from cop_thief.services.engine.board import Board


def test_get_set_cop_pos() -> None:
    """get_pos / set_pos works for cop."""
    b = Board(rows=5, cols=5)
    b.set_pos(Agent.COP, (1, 2))
    assert b.get_pos(Agent.COP) == (1, 2)


def test_get_set_thief_pos() -> None:
    """get_pos / set_pos works for thief."""
    b = Board(rows=5, cols=5)
    b.set_pos(Agent.THIEF, (3, 4))
    assert b.get_pos(Agent.THIEF) == (3, 4)


def test_reset_random_positions_distinct() -> None:
    """Random start positions are on distinct cells."""
    b = Board(rows=5, cols=5)
    rng = random.Random(42)
    b.reset(StartMode.RANDOM, rng, max_barriers=5)
    assert b.cop_pos != b.thief_pos


def test_reset_positions_in_bounds() -> None:
    """Start positions are within the grid."""
    b = Board(rows=5, cols=5)
    rng = random.Random(99)
    b.reset(StartMode.RANDOM, rng, max_barriers=5)
    assert b.in_bounds(b.cop_pos)
    assert b.in_bounds(b.thief_pos)


def test_reset_strategy_mode_corners() -> None:
    """Strategy mode places cop at (0,0) and thief at (rows-1, cols-1)."""
    b = Board(rows=5, cols=5)
    rng = random.Random(0)
    b.reset(StartMode.STRATEGY, rng, max_barriers=5)
    assert b.cop_pos == (0, 0)
    assert b.thief_pos == (4, 4)


def test_reset_clears_barriers() -> None:
    """reset() clears all barriers from the previous sub-game."""
    b = Board(rows=5, cols=5)
    b.place_barrier((1, 1))
    assert b.barriers_used == 1
    rng = random.Random(0)
    b.reset(StartMode.RANDOM, rng, max_barriers=5)
    assert b.barriers_used == 0
    assert len(b.barriers) == 0


def test_reset_deterministic_with_seed() -> None:
    """Same seed produces the same starting positions (NFR-11)."""
    b1 = Board(rows=5, cols=5)
    b2 = Board(rows=5, cols=5)
    rng1 = random.Random(12345)
    rng2 = random.Random(12345)
    b1.reset(StartMode.RANDOM, rng1, max_barriers=5)
    b2.reset(StartMode.RANDOM, rng2, max_barriers=5)
    assert b1.cop_pos == b2.cop_pos
    assert b1.thief_pos == b2.thief_pos


def test_all_free_cells_returns_all_on_empty_board() -> None:
    """all_free_cells returns all N*M cells when no barriers."""
    b = Board(rows=3, cols=4)
    free = b.all_free_cells()
    assert len(free) == 12  # noqa: PLR2004


def test_all_free_cells_excludes_barrier() -> None:
    """all_free_cells excludes barrier cells."""
    b = Board(rows=5, cols=5)
    b.place_barrier((2, 2))
    free = b.all_free_cells()
    assert (2, 2) not in free
    assert len(free) == 24  # noqa: PLR2004
