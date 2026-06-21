"""Single sub-game runner.

Factored out of :mod:`.lifecycle` to keep each file under ~150 LOC.

Traces: FR-L1, FR-M5, T-P1-17.
"""

from __future__ import annotations

import logging
import random
from collections.abc import Callable

from cop_thief.constants import Action, Agent, Outcome, StartMode
from cop_thief.services.engine._lifecycle_types import SubGameResult
from cop_thief.services.engine._turn_state import TurnState
from cop_thief.services.engine.board import Board
from cop_thief.services.engine.rules import RuleEngine
from cop_thief.services.engine.scoring import calculate_score
from cop_thief.shared._config_schemas import ScoringConfig

logger = logging.getLogger(__name__)

# Callable: receives board + current agent, returns an Action.
AgentDecider = Callable[[Board, Agent], Action]


def run_sub_game(
    board: Board,
    rules: RuleEngine,
    rng: random.Random,
    start_mode: StartMode,
    thief_moves_first: bool,
    scoring_config: ScoringConfig,
    cop_decider: AgentDecider,
    thief_decider: AgentDecider,
    sub_game_index: int,
) -> SubGameResult:
    """Run a single sub-game and return its result.

    Args:
        board: Board instance (mutated in-place).
        rules: :class:`RuleEngine` configured with limits.
        rng: Seeded RNG for deterministic start positions.
        start_mode: How to place agents at the start.
        thief_moves_first: Turn order flag.
        scoring_config: Points table from config.
        cop_decider: Returns a cop action given the board state.
        thief_decider: Returns a thief action given the board state.
        sub_game_index: 1-based index (for result labelling).

    Returns:
        A :class:`SubGameResult` for the completed sub-game.

    """
    board.reset(start_mode=start_mode, rng=rng, max_barriers=rules.max_barriers)
    turn = TurnState(thief_moves_first=thief_moves_first)

    logger.info(
        "Sub-game %d started: cop=%s thief=%s",
        sub_game_index, board.cop_pos, board.thief_pos,
    )

    outcome = Outcome.IN_PROGRESS

    while outcome is Outcome.IN_PROGRESS:
        agent = turn.current_agent
        decider = cop_decider if agent is Agent.COP else thief_decider
        action = decider(board, agent)

        move_result = rules.apply_action(board, agent, action)

        if move_result.outcome is Outcome.COP_WIN:
            outcome = Outcome.COP_WIN
            break

        turn.advance()

        # After both agents in a round have moved, check terminal conditions.
        if not turn._awaiting_second:  # noqa: SLF001
            outcome = rules.check_terminal(board, turn)

    score = calculate_score(outcome, scoring_config)
    result = SubGameResult(
        index=sub_game_index,
        winner=outcome,
        moves_used=turn.round_number,
        barriers_used=board.barriers_used,
        score=score,
    )
    logger.info(
        "Sub-game %d ended: winner=%s moves=%d barriers=%d cop_pts=%d thief_pts=%d",
        sub_game_index, outcome, result.moves_used, result.barriers_used,
        result.score.cop, result.score.thief,
    )
    return result
