"""Lifecycle determinism and retry edge-case tests."""

from __future__ import annotations

import random

from cop_thief.constants import Action, Agent, Outcome, StartMode
from cop_thief.services.engine.board import Board
from cop_thief.services.engine.lifecycle import run_full_game
from cop_thief.services.engine.rules import RuleEngine
from cop_thief.shared._config_schemas import ScoringConfig


def _stay(_board: Board, _agent: Agent) -> Action:
    return Action.STAY


def test_lifecycle_determinism() -> None:
    """Same seed produces identical game start positions and outcomes."""
    trace1 = _trace(42)
    trace2 = _trace(42)
    trace3 = _trace(43)
    assert trace1 == trace2
    assert trace3 != trace1
    assert len(trace1) == 3


def test_technical_failure_handling() -> None:
    """Exceptions during a sub-game trigger a retry and do not count as valid."""
    board = Board(rows=5, cols=5)
    rules = RuleEngine(max_barriers=5, max_moves=2)
    fail_counter = 0

    def failing_cop_decider(_board: Board, _agent: Agent) -> Action:
        nonlocal fail_counter
        if fail_counter < 2:
            fail_counter += 1
            raise RuntimeError("Simulation of agent decider crash")
        return Action.STAY

    full_result = run_full_game(
        board=board,
        rules=rules,
        rng=random.Random(99),
        start_mode=StartMode.STRATEGY,
        thief_moves_first=True,
        scoring_config=ScoringConfig(),
        cop_decider=failing_cop_decider,
        thief_decider=_stay,
        num_games=1,
    )
    assert fail_counter == 2
    assert len(full_result.sub_games) == 1
    assert full_result.totals.sub_game_count == 1


def _trace(seed: int) -> list[tuple[Outcome, int, int]]:
    board = Board(rows=5, cols=5)
    rules = RuleEngine(max_barriers=5, max_moves=20)
    rng = random.Random(seed)

    def rand_decider(_board: Board, _agent: Agent) -> Action:
        return rng.choice([Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT, Action.STAY])

    full_res = run_full_game(
        board=board,
        rules=rules,
        rng=rng,
        start_mode=StartMode.RANDOM,
        thief_moves_first=True,
        scoring_config=ScoringConfig(),
        cop_decider=rand_decider,
        thief_decider=rand_decider,
        num_games=3,
    )
    return [(game.winner, game.moves_used, game.barriers_used) for game in full_res.sub_games]
