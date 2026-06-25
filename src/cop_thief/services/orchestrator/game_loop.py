"""Sub-game and full-game drivers using MCP + LLM orchestration.

Traces: FR-L1, FR-L2, FR-L3, T-P3-09, T-P3-10.
"""

from __future__ import annotations

import random
from collections.abc import Callable

from cop_thief.constants import Outcome
from cop_thief.services.engine._board_helpers import choose_start_positions
from cop_thief.services.engine._lifecycle_types import FullGameResult, SubGameResult
from cop_thief.services.engine.scoring import calculate_score
from cop_thief.services.orchestrator._result_collector import ResultCollector
from cop_thief.services.orchestrator._snapshots import build_turn_frame
from cop_thief.services.orchestrator._turn_tracker import TurnTracker
from cop_thief.services.orchestrator._types import GameState
from cop_thief.services.orchestrator.mcp_client import McpClient
from cop_thief.services.orchestrator.turn_controller import TurnController, TurnResult
from cop_thief.shared.config import Config
from cop_thief.shared.logging import get_logger

_log = get_logger(__name__)
MAX_TURNS_PER_SUBGAME = 200  # safety cap (25 rounds × 2 agents)


class GameLoop:
    """Drive sub-games and full games through MCP tools."""

    def __init__(
        self,
        config: Config,
        mcp: McpClient,
        turn_controller: TurnController,
        rng: random.Random | None = None,
    ) -> None:
        """Wire config, MCP client, and turn controller."""
        self._cfg = config
        self._mcp = mcp
        self._turn = turn_controller
        self._rng = rng or random.Random(config.seed)
        self._estimator = turn_controller._estimator  # noqa: SLF001
        self._snapshots: list[GameState] = []

    @property
    def snapshots(self) -> list[GameState]:
        """Return GUI replay frames from the most recent sub-game."""
        return list(self._snapshots)

    async def _reset_sub_game(self) -> None:
        """Reset MCP state and place agents at new start positions."""
        status = await self._mcp.game_status()
        if status.get("over"):
            await self._mcp.update_position("cop", (0, 0))
        rows, cols = self._cfg.grid_size
        cop, thief = choose_start_positions(
            rows,
            cols,
            frozenset(),
            self._cfg.start_mode,
            self._rng,
        )
        await self._mcp.update_position("cop", cop)
        await self._mcp.update_position("thief", thief)
        self._estimator.reset(cop, thief)
        self._snapshots = [
            GameState(
                cop_pos=cop,
                thief_pos=thief,
                move_count=0,
                barriers_used=0,
                max_barriers=self._cfg.max_barriers,
                sub_game_index=0,
                grid_size=self._cfg.grid_size,
            ),
        ]

    def _append_snapshot(self, index: int, result: TurnResult, status: dict) -> GameState:
        """Append one GUI frame after a legal MCP turn."""
        frame = build_turn_frame(self._cfg, index, self._snapshots[-1], result, status)
        self._snapshots.append(frame)
        return frame

    async def run_sub_game(
        self,
        index: int,
        on_frame: Callable[[GameState], None] | None = None,
    ) -> SubGameResult:
        """Play one sub-game to completion via MCP."""
        await self._reset_sub_game()
        if on_frame:
            on_frame(self._snapshots[-1])
        self._turn.start_transcript(index)
        tracker = TurnTracker(self._cfg.thief_moves_first)
        turns = 0
        stalls = 0
        while turns < MAX_TURNS_PER_SUBGAME:
            status = await self._mcp.game_status()
            if status.get("over"):
                break
            agent = tracker.current_agent
            result = await self._turn.execute_turn(agent, status.get("move_count", 0))
            if result.legal:
                tracker.advance()
                stalls = 0
                post_status = await self._mcp.game_status()
                frame = self._append_snapshot(index, result, post_status)
                if on_frame:
                    on_frame(frame)
            else:
                stalls += 1
                if stalls > 4:  # noqa: PLR2004
                    raise RuntimeError("Turn stalled: MCP rejected repeated actions.")
            turns += 1
        status = await self._mcp.game_status()
        winner = Outcome(status["winner"]) if status.get("over") else Outcome.THIEF_WIN
        score = calculate_score(winner, self._cfg.scoring)
        return SubGameResult(
            index=index,
            winner=winner,
            moves_used=status.get("move_count", 0),
            barriers_used=status.get("barriers_used", 0),
            score=score,
        )

    async def run_full_game(
        self,
        on_frame: Callable[[GameState], None] | None = None,
    ) -> FullGameResult:
        """Run until *num_games* valid sub-games; rerun on technical failure."""
        collector = ResultCollector()
        attempts = 0
        while collector.count < self._cfg.num_games:
            attempts += 1
            sub_index = collector.count + 1
            try:
                result = await self.run_sub_game(sub_index, on_frame=on_frame)
            except Exception:  # noqa: BLE001
                _log.exception("Technical failure on sub-game %d; retrying.", sub_index)
                continue
            if result.winner not in (Outcome.COP_WIN, Outcome.THIEF_WIN):
                continue
            collector.add(result)
            _log.info("Valid sub-game %d/%d recorded.", collector.count, self._cfg.num_games)
        _log.info("Full game done in %d attempts.", attempts)
        return collector.to_full_result()
