"""Unit tests for NL-backed opponent estimation."""

from __future__ import annotations

from cop_thief.constants import Action, Agent
from cop_thief.services.orchestrator.estimator import OpponentEstimator


def test_estimator_updates_belief_from_nl_cue() -> None:
    estimator = OpponentEstimator((5, 5))
    estimator.reset((4, 4), (2, 2))
    estimator.update_from_message("I am hugging the north wall near the east side.", Agent.COP)
    assert estimator.estimate_for(Agent.COP)[0] < 2
    assert estimator.estimate_for(Agent.COP)[1] >= 2
    assert estimator.uncertainty_for(Agent.COP) < 1


def test_estimator_leaves_ambiguous_message_sane() -> None:
    estimator = OpponentEstimator((5, 5))
    estimator.reset((0, 0), (3, 3))
    before = estimator.estimate_for(Agent.COP)
    parsed = estimator.update_from_message("static and whispers", Agent.COP)
    assert parsed.ambiguous is True
    assert estimator.estimate_for(Agent.COP) == before


def test_estimator_fuses_move_history_for_observer() -> None:
    estimator = OpponentEstimator((5, 5))
    estimator.reset((0, 0), (4, 4))
    estimator.update_from_action(Agent.THIEF, Action.LEFT, (4, 3))
    assert estimator.estimate_for(Agent.COP) == (4, 3)
