"""Unit tests for RuleEngine victory and turn state logic.

Covers turn order, rounds, capture detection, and escape detection.
Traces: T-P1-22, T-P1-09, T-P1-13, T-P1-14, FR-M5, FR-V1, FR-V2, FR-V3.
"""

from __future__ import annotations

from cop_thief.constants import Action, Agent, Outcome
from cop_thief.services.engine.board import Board
from cop_thief.services.engine.rules import RuleEngine, TurnState


def make_board(cop: tuple[int, int], thief: tuple[int, int], rows: int = 5, cols: int = 5) -> Board:
    """Create a Board and manually set positions."""
    b = Board(rows=rows, cols=cols)
    b.cop_pos = cop
    b.thief_pos = thief
    return b


def make_rules(max_barriers: int = 5, max_moves: int = 25) -> RuleEngine:
    """Create a default RuleEngine."""
    return RuleEngine(max_barriers=max_barriers, max_moves=max_moves)


def test_turn_state_thief_first_default() -> None:
    """Default turn order: thief → cop → thief → cop …"""
    ts = TurnState(thief_moves_first=True)
    assert ts.current_agent == Agent.THIEF
    ts.advance()
    assert ts.current_agent == Agent.COP
    ts.advance()
    assert ts.round_number == 1
    assert ts.current_agent == Agent.THIEF


def test_turn_state_cop_first() -> None:
    """Alternative turn order: cop → thief …"""
    ts = TurnState(thief_moves_first=False)
    assert ts.current_agent == Agent.COP
    ts.advance()
    assert ts.current_agent == Agent.THIEF
    ts.advance()
    assert ts.round_number == 1
    assert ts.current_agent == Agent.COP


def test_turn_state_round_increments_correctly() -> None:
    """round_number increments exactly once per full round."""
    ts = TurnState(thief_moves_first=True)
    assert ts.round_number == 0
    ts.advance()
    assert ts.round_number == 0
    ts.advance()
    assert ts.round_number == 1
    ts.advance()
    assert ts.round_number == 1
    ts.advance()
    assert ts.round_number == 2


def test_capture_when_cop_moves_to_thief() -> None:
    """Moving cop onto thief's cell returns COP_WIN outcome."""
    b = make_board(cop=(2, 1), thief=(2, 2))
    rules = make_rules()
    result = rules.apply_action(b, Agent.COP, Action.RIGHT)
    assert result.outcome is Outcome.COP_WIN
    assert b.cop_pos == b.thief_pos == (2, 2)


def test_capture_when_thief_moves_to_cop() -> None:
    """Moving thief onto cop's cell returns COP_WIN outcome."""
    b = make_board(cop=(2, 2), thief=(2, 1))
    rules = make_rules()
    result = rules.apply_action(b, Agent.THIEF, Action.RIGHT)
    assert result.outcome is Outcome.COP_WIN


def test_no_capture_after_legal_move_away() -> None:
    """Normal move without capture returns IN_PROGRESS outcome."""
    b = make_board(cop=(2, 2), thief=(4, 4))
    rules = make_rules()
    result = rules.apply_action(b, Agent.COP, Action.UP)
    assert result.outcome is None


def test_escape_at_max_moves() -> None:
    """check_terminal returns THIEF_WIN when round_number >= max_moves."""
    b = make_board(cop=(0, 0), thief=(4, 4))
    rules = make_rules(max_moves=25)
    ts = TurnState()
    ts.round_number = 25
    outcome = rules.check_terminal(b, ts)
    assert outcome is Outcome.THIEF_WIN


def test_in_progress_before_max_moves() -> None:
    """check_terminal returns IN_PROGRESS when neither condition met."""
    b = make_board(cop=(0, 0), thief=(4, 4))
    rules = make_rules(max_moves=25)
    ts = TurnState()
    ts.round_number = 10
    outcome = rules.check_terminal(b, ts)
    assert outcome is Outcome.IN_PROGRESS


def test_capture_detected_by_check_terminal() -> None:
    """check_terminal detects capture (same cell)."""
    b = make_board(cop=(2, 2), thief=(2, 2))
    rules = make_rules()
    ts = TurnState()
    outcome = rules.check_terminal(b, ts)
    assert outcome is Outcome.COP_WIN
