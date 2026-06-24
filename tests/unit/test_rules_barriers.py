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


def test_cop_places_barrier_and_relocates_off_blocked_cell() -> None:
    """Cop's place_barrier blocks the current cell and relocates the cop."""
    b = make_board(cop=(2, 2), thief=(4, 4))
    rules = make_rules()
    result = rules.apply_action(b, Agent.COP, Action.PLACE_BARRIER)
    assert result.legal is True
    assert result.barrier_placed is True
    assert b.is_blocked((2, 2)) is True
    assert b.cop_pos == (1, 2)
    assert result.new_pos == (1, 2)
    assert b.is_blocked(b.cop_pos) is False
    assert b.barriers_used == 1


def test_cop_barrier_relocation_uses_next_legal_adjacent_cell() -> None:
    """Relocation skips blocked adjacent cells deterministically."""
    b = make_board(cop=(1, 1), thief=(4, 4))
    b.place_barrier((0, 1))
    rules = make_rules()
    result = rules.apply_action(b, Agent.COP, Action.PLACE_BARRIER)
    assert result.legal is True
    assert b.cop_pos == (2, 1)
    assert b.is_blocked((1, 1)) is True
    assert b.barriers_used == 2


def test_duplicate_barrier_rejected_without_consuming_budget() -> None:
    """A second barrier on the same cell is rejected and leaves budget unchanged."""
    b = make_board(cop=(2, 2), thief=(4, 4))
    b.place_barrier((2, 2))
    before = b.barriers_used
    rules = make_rules()
    result = rules.apply_action(b, Agent.COP, Action.PLACE_BARRIER)
    assert result.legal is False
    assert "already exists" in (result.rejection_reason or "")
    assert b.barriers_used == before


def test_place_barrier_rejected_when_cop_cannot_relocate() -> None:
    """Barrier placement is atomic when no adjacent legal relocation exists."""
    b = make_board(cop=(1, 1), thief=(0, 0), rows=3, cols=3)
    b.barriers = frozenset(
        {
            (0, 1),
            (0, 2),
            (1, 0),
            (1, 2),
            (2, 0),
            (2, 1),
            (2, 2),
        }
    )
    b.barriers_used = len(b.barriers)
    rules = make_rules(max_barriers=8)
    result = rules.apply_action(b, Agent.COP, Action.PLACE_BARRIER)
    assert result.legal is False
    assert "No legal relocation" in (result.rejection_reason or "")
    assert b.is_blocked((1, 1)) is False
    assert b.cop_pos == (1, 1)
    assert b.barriers_used == 7


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
