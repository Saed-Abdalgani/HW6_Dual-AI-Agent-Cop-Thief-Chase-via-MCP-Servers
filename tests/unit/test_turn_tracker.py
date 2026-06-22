"""Unit tests for orchestrator turn order tracking."""

from __future__ import annotations

from cop_thief.constants import Agent
from cop_thief.services.orchestrator._turn_tracker import TurnTracker


def test_thief_moves_first_order() -> None:
    tracker = TurnTracker(thief_moves_first=True)
    assert tracker.current_agent is Agent.THIEF
    tracker.advance()
    assert tracker.current_agent is Agent.COP
    tracker.advance()
    assert tracker.round_number == 1
    assert tracker.current_agent is Agent.THIEF


def test_cop_moves_first_order() -> None:
    tracker = TurnTracker(thief_moves_first=False)
    assert tracker.current_agent is Agent.COP
    tracker.advance()
    assert tracker.current_agent is Agent.THIEF
