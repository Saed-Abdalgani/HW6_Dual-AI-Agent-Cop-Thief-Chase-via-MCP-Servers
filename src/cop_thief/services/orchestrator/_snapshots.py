"""GUI snapshot construction helpers for GameLoop."""

from __future__ import annotations

from cop_thief.services.orchestrator._types import GameState
from cop_thief.services.orchestrator.turn_controller import TurnResult
from cop_thief.shared.config import Config


def build_turn_frame(
    config: Config,
    index: int,
    previous: GameState,
    result: TurnResult,
    status: dict,
) -> GameState:
    """Build a GUI frame after a legal MCP turn."""
    cop_pos, thief_pos = previous.cop_pos, previous.thief_pos
    if result.new_pos and result.agent.value == "cop":
        cop_pos = result.new_pos
    if result.new_pos and result.agent.value == "thief":
        thief_pos = result.new_pos
    return GameState(
        cop_pos=cop_pos,
        thief_pos=thief_pos,
        barriers=[tuple(item) for item in status.get("barriers", previous.barriers)],
        move_count=status.get("move_count", previous.move_count),
        barriers_used=status.get("barriers_used", previous.barriers_used),
        max_barriers=config.max_barriers,
        over=status.get("over", False),
        winner=status.get("winner"),
        scores=status.get("scores", previous.scores),
        sub_game_index=index,
        latest_message=result.nl_message,
        grid_size=config.grid_size,
    )
