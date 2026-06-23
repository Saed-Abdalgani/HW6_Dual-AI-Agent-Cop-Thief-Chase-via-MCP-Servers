"""Implementation functions for Cop and Thief MCP tools."""

from __future__ import annotations

import uuid

from cop_thief.constants import MOVE_DELTAS, Action, Agent
from cop_thief.mcp_servers._state import (
    get_engine_objects,
    load_state,
    save_state,
    update_state_from_engine,
)
from cop_thief.shared.auth import default_store
from cop_thief.shared.config import Config


def authorize(token: str, expected_agent: str | None = None) -> str:
    """Validate token and optional agent ownership."""
    agent = default_store.get_agent(token)
    if not agent:
        raise ValueError("Unauthorized: Invalid or missing token")
    if expected_agent and agent != expected_agent:
        raise ValueError(f"Unauthorized: Token does not belong to {expected_agent}")
    return agent


def send_message(from_agent: str, text: str, token: str) -> dict:
    """Send a free-text message to the opponent."""
    authorize(token, expected_agent=from_agent)
    if from_agent not in ("cop", "thief"):
        raise ValueError(f"Invalid agent '{from_agent}'")
    state = load_state()
    msg_id = str(uuid.uuid4())
    state["messages"].append({"from_agent": from_agent, "text": text, "msg_id": msg_id})
    save_state(state)
    return {"ok": True, "msg_id": msg_id}


def receive_message(for_agent: str, token: str) -> dict:
    """Retrieve the latest message for the agent."""
    authorize(token, expected_agent=for_agent)
    if for_agent not in ("cop", "thief"):
        raise ValueError(f"Invalid agent '{for_agent}'")
    state = load_state()
    opponent = "thief" if for_agent == "cop" else "cop"
    opp_msgs = [m for m in state["messages"] if m["from_agent"] == opponent]
    if opp_msgs:
        return {"text": opp_msgs[-1]["text"], "msg_id": opp_msgs[-1]["msg_id"]}
    return {"text": "", "msg_id": ""}


def update_position(agent: str, pos: list[int] | tuple[int, int], token: str) -> dict:
    """Update the agent's position on the board."""
    authorize(token, expected_agent=agent)
    if agent not in ("cop", "thief"):
        raise ValueError(f"Invalid agent '{agent}'")
    if not isinstance(pos, (list, tuple)) or len(pos) != 2:
        raise ValueError("Position must be a 2-element list/tuple [row, col]")
    state = load_state()
    if state["over"]:
        config = Config.from_env()
        state = {
            "cop_pos": [0, 0],
            "thief_pos": [config.grid_size[0] - 1, config.grid_size[1] - 1],
            "barriers": [],
            "barriers_used": 0,
            "messages": [],
            "round_number": 0,
            "awaiting_second": False,
            "over": False,
            "winner": "in_progress",
        }
    board, turn, rules = get_engine_objects(state)
    ag = Agent.COP if agent == "cop" else Agent.THIEF
    target = tuple(pos)
    if not board.is_legal_cell(target):
        raise ValueError(f"Position {target} is blocked or out-of-bounds.")
    board.set_pos(ag, target)
    update_state_from_engine(state, board, turn, rules)
    save_state(state)
    return {"ok": True, "pos": list(board.get_pos(ag))}


def verify_position(agent: str, token: str) -> dict:
    """Retrieve the current position of the agent."""
    authorize(token, expected_agent=agent)
    if agent not in ("cop", "thief"):
        raise ValueError(f"Invalid agent '{agent}'")
    state = load_state()
    return {"pos": state["cop_pos"] if agent == "cop" else state["thief_pos"]}


def choose_action(agent: str, observation: dict, token: str) -> dict:
    """Pick a legal action for the agent."""
    authorize(token, expected_agent=agent)
    if agent not in ("cop", "thief"):
        raise ValueError(f"Invalid agent '{agent}'")
    state = load_state()
    board, _turn, _rules = get_engine_objects(state)
    ag = Agent.COP if agent == "cop" else Agent.THIEF
    curr_pos = board.get_pos(ag)
    for act, delta in MOVE_DELTAS.items():
        tgt = (curr_pos[0] + delta[0], curr_pos[1] + delta[1])
        if board.is_legal_cell(tgt):
            return {"action": act.value}
    return {"action": "stay"}


def apply_action(agent: str, action: str, token: str) -> dict:
    """Resolve and execute the agent's action."""
    authorize(token, expected_agent=agent)
    if agent not in ("cop", "thief"):
        raise ValueError(f"Invalid agent '{agent}'")
    try:
        act = Action(action)
    except ValueError:
        return {"legal": False, "rejection_reason": f"Invalid action '{action}'"}
    state = load_state()
    board, turn, rules = get_engine_objects(state)
    ag = Agent.COP if agent == "cop" else Agent.THIEF
    if turn.current_agent is not ag:
        return {"legal": False, "rejection_reason": "Not your turn"}
    move_result = rules.apply_action(board, ag, act)
    if not move_result.legal:
        return {"legal": False, "rejection_reason": move_result.rejection_reason}
    turn.advance()
    update_state_from_engine(state, board, turn, rules)
    save_state(state)
    return {
        "legal": True,
        "state_delta": {
            "new_pos": list(board.get_pos(ag)),
            "barrier_placed": move_result.barrier_placed,
            "over": state["over"],
            "winner": state["winner"],
        },
    }
