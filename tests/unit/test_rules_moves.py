"""Unit tests for RuleEngine move resolution.

Covers directional moves, staying in place, and out-of-bounds rejection.
Traces: T-P1-20, T-P1-06, T-P1-07, FR-M1, FR-M2, FR-M3.
"""

from __future__ import annotations

import pytest

from cop_thief.constants import Action, Agent
from cop_thief.services.engine.board import Board
from cop_thief.services.engine.rules import RuleEngine


def make_board(cop: tuple[int, int], thief: tuple[int, int], rows: int = 5, cols: int = 5) -> Board:
    """Create a Board and manually set positions."""
    b = Board(rows=rows, cols=cols)
    b.cop_pos = cop
    b.thief_pos = thief
    return b


def make_rules(max_barriers: int = 5, max_moves: int = 25) -> RuleEngine:
    """Create a default RuleEngine."""
    return RuleEngine(max_barriers=max_barriers, max_moves=max_moves)


@pytest.mark.parametrize(
    ("action", "start", "expected"),
    [
        (Action.UP, (2, 2), (1, 2)),
        (Action.DOWN, (2, 2), (3, 2)),
        (Action.LEFT, (2, 2), (2, 1)),
        (Action.RIGHT, (2, 2), (2, 3)),
        (Action.UP_LEFT, (2, 2), (1, 1)),
        (Action.UP_RIGHT, (2, 2), (1, 3)),
        (Action.DOWN_LEFT, (2, 2), (3, 1)),
        (Action.DOWN_RIGHT, (2, 2), (3, 3)),
        (Action.STAY, (2, 2), (2, 2)),
    ],
)
def test_cop_directional_moves(
    action: Action, start: tuple[int, int], expected: tuple[int, int]
) -> None:
    """Each directional move produces the correct target cell."""
    b = make_board(cop=start, thief=(4, 4))
    rules = make_rules()
    result = rules.apply_action(b, Agent.COP, action)
    assert result.legal is True
    assert result.new_pos == expected
    assert b.cop_pos == expected


def test_thief_stay_move() -> None:
    """Thief can stay in place."""
    b = make_board(cop=(0, 0), thief=(2, 2))
    rules = make_rules()
    result = rules.apply_action(b, Agent.THIEF, Action.STAY)
    assert result.legal is True
    assert b.thief_pos == (2, 2)


def test_reject_move_off_top() -> None:
    """Moving UP from row 0 is rejected."""
    b = make_board(cop=(0, 2), thief=(4, 4))
    rules = make_rules()
    result = rules.apply_action(b, Agent.COP, Action.UP)
    assert result.legal is False
    assert b.cop_pos == (0, 2)


def test_reject_move_off_left() -> None:
    """Moving LEFT from col 0 is rejected."""
    b = make_board(cop=(2, 0), thief=(4, 4))
    rules = make_rules()
    result = rules.apply_action(b, Agent.COP, Action.LEFT)
    assert result.legal is False
    assert b.cop_pos == (2, 0)


def test_reject_move_off_bottom() -> None:
    """Moving DOWN from the last row is rejected."""
    b = make_board(cop=(4, 2), thief=(0, 0))
    rules = make_rules()
    result = rules.apply_action(b, Agent.COP, Action.DOWN)
    assert result.legal is False
    assert b.cop_pos == (4, 2)


def test_reject_move_off_right() -> None:
    """Moving RIGHT from the last col is rejected."""
    b = make_board(cop=(2, 4), thief=(0, 0))
    rules = make_rules()
    result = rules.apply_action(b, Agent.COP, Action.RIGHT)
    assert result.legal is False
    assert b.cop_pos == (2, 4)


def test_reject_diagonal_off_grid() -> None:
    """Diagonal move off the grid is rejected."""
    b = make_board(cop=(0, 0), thief=(4, 4))
    rules = make_rules()
    result = rules.apply_action(b, Agent.COP, Action.UP_LEFT)
    assert result.legal is False
