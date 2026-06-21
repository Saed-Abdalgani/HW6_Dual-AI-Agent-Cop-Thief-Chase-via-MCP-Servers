"""Unit tests for RuleEngine barrier enforcement.

Covers barrier-crossing rejection, cop barrier placement, maximum barrier limits,
and thief barrier placement prohibition.
Traces: T-P1-21, T-P1-08, T-P1-10, T-P1-11, T-P1-12, FR-M4, FR-BR1, FR-BR2, FR-BR4, FR-BR5.
"""

from __future__ import annotations

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


def test_reject_move_into_barrier_cop() -> None:
    """Cop cannot move into a barrier cell."""
    b = make_board(cop=(2, 2), thief=(4, 4))
    b.place_barrier((1, 2))  # place barrier directly above cop
    rules = make_rules()
    result = rules.apply_action(b, Agent.COP, Action.UP)
    assert result.legal is False
    assert b.cop_pos == (2, 2)


def test_reject_move_into_barrier_thief() -> None:
    """Thief cannot move into a barrier cell."""
    b = make_board(cop=(0, 0), thief=(2, 2))
    b.place_barrier((1, 2))  # place barrier above thief
    rules = make_rules()
    result = rules.apply_action(b, Agent.THIEF, Action.UP)
    assert result.legal is False
    assert b.thief_pos == (2, 2)


def test_thief_cannot_place_barrier() -> None:
    """Thief's place_barrier action is rejected."""
    b = make_board(cop=(0, 0), thief=(2, 2))
    rules = make_rules()
    result = rules.apply_action(b, Agent.THIEF, Action.PLACE_BARRIER)
    assert result.legal is False
    assert b.barriers_used == 0


def test_cop_places_barrier_on_current_cell() -> None:
    """Cop's place_barrier blocks the cop's current cell."""
    b = make_board(cop=(2, 2), thief=(4, 4))
    rules = make_rules()
    result = rules.apply_action(b, Agent.COP, Action.PLACE_BARRIER)
    assert result.legal is True
    assert result.barrier_placed is True
    assert b.cop_pos == (2, 2)
    assert b.is_blocked((2, 2)) is True
    assert b.barriers_used == 1


def test_cop_does_not_move_when_placing_barrier() -> None:
    """Cop position is unchanged after barrier placement."""
    b = make_board(cop=(1, 1), thief=(4, 4))
    rules = make_rules()
    rules.apply_action(b, Agent.COP, Action.PLACE_BARRIER)
    assert b.cop_pos == (1, 1)


def test_sixth_barrier_rejected() -> None:
    """A 6th barrier placement is rejected when max_barriers=5."""
    b = make_board(cop=(2, 2), thief=(4, 4))
    b.barriers_used = 5
    rules = make_rules(max_barriers=5)
    result = rules.apply_action(b, Agent.COP, Action.PLACE_BARRIER)
    assert result.legal is False
    assert b.barriers_used == 5


def test_exactly_max_barriers_allowed() -> None:
    """The max_barriers-th barrier is still accepted."""
    rules = make_rules(max_barriers=5)
    for r in range(5):
        b_inner = make_board(cop=(r, 0), thief=(4, 4))
        b_inner.barriers_used = r
        res = rules.apply_action(b_inner, Agent.COP, Action.PLACE_BARRIER)
        assert res.legal is True
