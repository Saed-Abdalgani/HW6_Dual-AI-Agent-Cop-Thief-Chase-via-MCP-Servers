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


def test_lifecycle_determinism() -> None:
    """Same seed produces identical game start positions and outcomes."""
    scoring_config = ScoringConfig()

    def run_one(seed: int) -> list[tuple[Outcome, int, int]]:
        board = Board(rows=5, cols=5)
        rules = RuleEngine(max_barriers=5, max_moves=20)
        rng = random.Random(seed)

        def rand_decider(board: Board, agent: Agent) -> Action:  # noqa: ARG001
            return rng.choice([Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT, Action.STAY])

        full_res = run_full_game(
            board=board,
            rules=rules,
            rng=rng,
            start_mode=StartMode.RANDOM,
            thief_moves_first=True,
            scoring_config=scoring_config,
            cop_decider=rand_decider,
            thief_decider=rand_decider,
            num_games=3,
        )
        return [(g.winner, g.moves_used, g.barriers_used) for g in full_res.sub_games]

    trace1 = run_one(42)
    trace2 = run_one(42)
    trace3 = run_one(43)

    assert trace1 == trace2
    assert trace3 != trace1
    assert len(trace1) == 3


def test_technical_failure_handling() -> None:
    """Exceptions during a sub-game trigger a retry and do not count as valid."""
    board = Board(rows=5, cols=5)
    rules = RuleEngine(max_barriers=5, max_moves=2)
    rng = random.Random(99)
    scoring_config = ScoringConfig()

    fail_counter = 0

    def failing_cop_decider(board: Board, agent: Agent) -> Action:  # noqa: ARG001
        nonlocal fail_counter
        if fail_counter < 2:
            fail_counter += 1
            msg = "Simulation of agent decider crash"
            raise RuntimeError(msg)
        return Action.STAY

    full_result = run_full_game(
        board=board,
        rules=rules,
        rng=rng,
        start_mode=StartMode.STRATEGY,
        thief_moves_first=True,
        scoring_config=scoring_config,
        cop_decider=failing_cop_decider,
        thief_decider=dummy_thief_decider,
        num_games=1,
    )
    assert fail_counter == 2
    assert len(full_result.sub_games) == 1
    assert full_result.totals.sub_game_count == 1
