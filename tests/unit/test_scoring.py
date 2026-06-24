"""Unit tests for the scoring system.

Covers sub-game score calculations, cumulative score accumulation,
and error handling on invalid outcomes.
Traces: T-P1-23, T-P1-15, T-P1-16, FR-S1, FR-S2, FR-S3.
"""

from __future__ import annotations

import pytest

from cop_thief.constants import Outcome
from cop_thief.services.engine.scoring import ScoreTotals, SubGameScore, calculate_score
from cop_thief.shared._config_schemas import ScoringConfig


def test_sub_game_score_properties() -> None:
    """SubGameScore holds cop and thief scores correctly."""
    score = SubGameScore(cop=15, thief=8)
    assert score.cop == 15
    assert score.thief == 8


def test_score_totals_initial_state() -> None:
    """ScoreTotals starts with zero values."""
    totals = ScoreTotals()
    assert totals.cop == 0
    assert totals.thief == 0
    assert totals.sub_game_count == 0


def test_score_totals_accumulation() -> None:
    """ScoreTotals accumulates points correctly."""
    totals = ScoreTotals()
    totals.add(SubGameScore(cop=20, thief=5))
    assert totals.cop == 20
    assert totals.thief == 5
    assert totals.sub_game_count == 1

    totals.add(SubGameScore(cop=5, thief=10))
    assert totals.cop == 25
    assert totals.thief == 15
    assert totals.sub_game_count == 2


def test_prd_role_balanced_six_game_score_bounds() -> None:
    """Document PRD group bounds for a 3-cop/3-thief role-balanced match."""
    config = ScoringConfig()
    group_max = (3 * config.cop_win) + (3 * config.thief_win)
    thief_escape_ceiling = 6 * config.thief_win
    assert group_max == 90  # noqa: PLR2004
    assert thief_escape_ceiling == 60  # noqa: PLR2004


def test_calculate_score_cop_win() -> None:
    """calculate_score returns correct scores for a cop win."""
    config = ScoringConfig(cop_win=20, thief_win=10, cop_loss=5, thief_loss=3)
    score = calculate_score(Outcome.COP_WIN, config)
    assert score.cop == 20
    assert score.thief == 3


def test_calculate_score_thief_win() -> None:
    """calculate_score returns correct scores for a thief win."""
    config = ScoringConfig(cop_win=20, thief_win=10, cop_loss=5, thief_loss=3)
    score = calculate_score(Outcome.THIEF_WIN, config)
    assert score.cop == 5
    assert score.thief == 10


def test_calculate_score_invalid_outcome() -> None:
    """calculate_score raises ValueError for non-terminal outcomes."""
    config = ScoringConfig()
    with pytest.raises(ValueError, match="Cannot calculate score for non-terminal outcome"):
        calculate_score(Outcome.IN_PROGRESS, config)
