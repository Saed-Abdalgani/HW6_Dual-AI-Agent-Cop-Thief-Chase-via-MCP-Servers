"""Full-game lifecycle: loop until *num_games* valid sub-games complete.

Imports result types from :mod:`._lifecycle_types` and the sub-game runner
from :mod:`._sub_game_runner` to stay under ~150 LOC.

Traces: FR-L2, FR-L3, T-P1-18, T-P1-19.
"""

from __future__ import annotations

import logging
import random

from cop_thief.constants import Outcome, StartMode
from cop_thief.services.engine._lifecycle_types import FullGameResult, SubGameResult
from cop_thief.services.engine._sub_game_runner import AgentDecider, run_sub_game
from cop_thief.services.engine.board import Board
from cop_thief.services.engine.rules import RuleEngine
from cop_thief.shared._config_schemas import ScoringConfig

# Re-export so ``from cop_thief.services.engine.lifecycle import …`` keeps working.
__all__ = [
    "AgentDecider",
    "FullGameResult",
    "SubGameResult",
    "run_full_game",
    "run_sub_game",
]

logger = logging.getLogger(__name__)


def run_full_game(
    board: Board,
    rules: RuleEngine,
    rng: random.Random,
    start_mode: StartMode,
    thief_moves_first: bool,
    scoring_config: ScoringConfig,
    cop_decider: AgentDecider,
    thief_decider: AgentDecider,
    num_games: int = 6,
) -> FullGameResult:
    """Run until exactly *num_games* valid sub-games have completed.

    A sub-game is **valid** when it ends with ``COP_WIN`` or ``THIEF_WIN``.
    On :class:`Exception` (technical failure) the sub-game is logged,
    excluded, and immediately retried.

    Args:
        board: Shared board instance (reset per sub-game).
        rules: Rule engine configured with config limits.
        rng: Seeded RNG shared across all sub-games.
        start_mode: Agent placement mode per sub-game.
        thief_moves_first: Turn order flag.
        scoring_config: Points table.
        cop_decider: Cop action provider.
        thief_decider: Thief action provider.
        num_games: Number of **valid** sub-games to collect (default 6).

    Returns:
        A :class:`FullGameResult` with exactly *num_games* valid sub-games.

    """
    full_result = FullGameResult()
    attempt = 0

    while len(full_result.sub_games) < num_games:
        attempt += 1
        sub_index = len(full_result.sub_games) + 1

        try:
            result = run_sub_game(
                board=board,
                rules=rules,
                rng=rng,
                start_mode=start_mode,
                thief_moves_first=thief_moves_first,
                scoring_config=scoring_config,
                cop_decider=cop_decider,
                thief_decider=thief_decider,
                sub_game_index=sub_index,
            )
        except Exception:  # noqa: BLE001
            logger.exception(
                "Technical failure in sub-game attempt %d (slot %d); retrying.",
                attempt, sub_index,
            )
            continue

        if result.winner not in (Outcome.COP_WIN, Outcome.THIEF_WIN):
            logger.error(
                "Sub-game attempt %d produced non-terminal outcome %s; retrying.",
                attempt, result.winner,
            )
            continue

        full_result.add(result)
        logger.info(
            "Valid sub-game %d/%d collected (attempt %d).",
            len(full_result.sub_games), num_games, attempt,
        )

    logger.info(
        "Full game complete: %d valid sub-games in %d attempts. "
        "Totals: cop=%d thief=%d.",
        num_games, attempt, full_result.totals.cop, full_result.totals.thief,
    )
    return full_result
