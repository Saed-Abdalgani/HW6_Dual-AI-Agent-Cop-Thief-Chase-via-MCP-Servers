"""Unit tests for sub-game and full-game lifecycle runners.

Covers execution of single/multiple sub-games, scoring accumulation,
determinism (seed validation), and retry behaviors on technical failures.
Traces: T-P1-24, T-P1-25, T-P1-17, T-P1-18, T-P1-19, FR-L1, FR-L2, FR-L3, NFR-4, NFR-11.
"""

from __future__ import annotations

import random

from cop_thief.constants import Action, Agent, Outcome, StartMode
from cop_thief.services.engine.board import Board
from cop_thief.services.engine.lifecycle import run_full_game, run_sub_game
from cop_thief.services.engine.rules import RuleEngine
from cop_thief.shared._config_schemas import ScoringConfig


def dummy_cop_decider(board: Board, agent: Agent) -> Action:  # noqa: ARG001
    """Always return stay to let thief escape or do whatever."""
    return Action.STAY


def dummy_thief_decider(board: Board, agent: Agent) -> Action:  # noqa: ARG001
    """Always return stay."""
    return Action.STAY


def test_run_sub_game_success() -> None:
    """run_sub_game runs a game to completion (thief escape on stay)."""
    board = Board(rows=5, cols=5)
    rules = RuleEngine(max_barriers=5, max_moves=2)
    rng = random.Random(42)
    scoring_config = ScoringConfig()

    result = run_sub_game(
        board=board,
        rules=rules,
        rng=rng,
        start_mode=StartMode.STRATEGY,
        thief_moves_first=True,
        scoring_config=scoring_config,
        cop_decider=dummy_cop_decider,
        thief_decider=dummy_thief_decider,
        sub_game_index=1,
    )
    assert result.index == 1
    assert result.winner == Outcome.THIEF_WIN
    assert result.moves_used == 2
    assert result.barriers_used == 0
    assert result.score.cop == scoring_config.cop_loss
    assert result.score.thief == scoring_config.thief_win


def test_run_full_game_success() -> None:
    """run_full_game collects exactly the requested number of valid games."""
    board = Board(rows=5, cols=5)
    rules = RuleEngine(max_barriers=5, max_moves=2)
    rng = random.Random(123)
    scoring_config = ScoringConfig()

    full_result = run_full_game(
        board=board,
        rules=rules,
        rng=rng,
        start_mode=StartMode.RANDOM,
        thief_moves_first=True,
        scoring_config=scoring_config,
        cop_decider=dummy_cop_decider,
        thief_decider=dummy_thief_decider,
        num_games=3,
    )
    assert len(full_result.sub_games) == 3
    assert full_result.totals.sub_game_count == 3
    assert all(g.winner == Outcome.THIEF_WIN for g in full_result.sub_games)


def test_run_full_game_default_collects_six_valid_games() -> None:
    """The default full-game length is exactly 6 valid sub-games."""
    board = Board(rows=5, cols=5)
    rules = RuleEngine(max_barriers=5, max_moves=1)
    rng = random.Random(123)
    scoring_config = ScoringConfig()

    full_result = run_full_game(
        board=board,
        rules=rules,
        rng=rng,
        start_mode=StartMode.RANDOM,
        thief_moves_first=True,
        scoring_config=scoring_config,
        cop_decider=dummy_cop_decider,
        thief_decider=dummy_thief_decider,
    )
    assert len(full_result.sub_games) == 6  # noqa: PLR2004
    assert full_result.totals.sub_game_count == 6  # noqa: PLR2004


def test_illegal_move_still_advances_turn_and_round() -> None:
    """A rejected half-turn still advances the lifecycle turn tracker."""
    board = Board(rows=5, cols=5)
    rules = RuleEngine(max_barriers=5, max_moves=1)
    rng = random.Random(0)
    scoring_config = ScoringConfig()

    result = run_sub_game(
        board=board,
        rules=rules,
        rng=rng,
        start_mode=StartMode.STRATEGY,
        thief_moves_first=True,
        scoring_config=scoring_config,
        cop_decider=lambda _board, _agent: Action.UP,
        thief_decider=dummy_thief_decider,
        sub_game_index=1,
    )
    assert result.winner == Outcome.THIEF_WIN
    assert result.moves_used == 1
