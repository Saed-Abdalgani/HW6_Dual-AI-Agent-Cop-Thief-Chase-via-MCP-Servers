"""Tactical analysis for LLM prompts (partial-obs pursuit / evasion).

Computes ranked action hints from :class:`Observation` without ground truth.
Traces: FR-LLM1, FR-NL2, T-P5-01.
"""

from __future__ import annotations

from dataclasses import dataclass

from cop_thief.constants import COP_ACTIONS, MOVE_DELTAS, THIEF_ACTIONS, Action, Agent
from cop_thief.services.orchestrator._thief_apf import (
    build_belief_map,
    choose_thief_action,
    potential_at,
    thief_apf_score,
)
from cop_thief.services.orchestrator._types import Observation


@dataclass(frozen=True)
class ActionHint:
    """One scored candidate action with a short rationale."""

    action: Action
    score: float
    reason: str


def _manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _target(obs: Observation, action: Action) -> tuple[int, int]:
    dr, dc = MOVE_DELTAS[action]
    r, c = obs.own_pos
    return (r + dr, c + dc)


def _in_bounds(pos: tuple[int, int], rows: int, cols: int) -> bool:
    return 0 <= pos[0] < rows and 0 <= pos[1] < cols


def _mobility(pos: tuple[int, int], obs: Observation) -> int:
    rows, cols = obs.grid_size
    count = 0
    for action, (dr, dc) in MOVE_DELTAS.items():
        if action is Action.STAY:
            continue
        nxt = (pos[0] + dr, pos[1] + dc)
        if _in_bounds(nxt, rows, cols) and nxt not in obs.barriers:
            count += 1
    return count


def _border_distance(pos: tuple[int, int], rows: int, cols: int) -> int:
    """Minimum steps from *pos* to any board edge."""
    r, c = pos
    return min(r, rows - 1 - r, c, cols - 1 - c)


def _is_edge_cell(pos: tuple[int, int], rows: int, cols: int) -> bool:
    r, c = pos
    return r in (0, rows - 1) or c in (0, cols - 1)


def _is_corner_cell(pos: tuple[int, int], rows: int, cols: int) -> bool:
    r, c = pos
    return (r in (0, rows - 1)) and (c in (0, cols - 1))


def _edge_penalty(pos: tuple[int, int], rows: int, cols: int) -> int:
    r, c = pos
    return int(r in (0, rows - 1)) + int(c in (0, cols - 1))


def action_target(obs: Observation, action: Action) -> tuple[int, int]:
    """Return the cell *action* would land on."""
    return _target(obs, action)


def is_edge_cell(pos: tuple[int, int], rows: int, cols: int) -> bool:
    return _is_edge_cell(pos, rows, cols)


def is_corner_cell(pos: tuple[int, int], rows: int, cols: int) -> bool:
    return _is_corner_cell(pos, rows, cols)


def border_distance(pos: tuple[int, int], rows: int, cols: int) -> int:
    return _border_distance(pos, rows, cols)


def _legal_moves(obs: Observation) -> list[Action]:
    rows, cols = obs.grid_size
    pool = THIEF_ACTIONS if obs.agent is Agent.THIEF else COP_ACTIONS
    legal: list[Action] = []
    for action in pool:
        if action is Action.PLACE_BARRIER:
            continue
        nxt = _target(obs, action)
        if _in_bounds(nxt, rows, cols) and nxt not in obs.barriers:
            legal.append(action)
    return legal or [Action.STAY]


def _can_place_barrier(obs: Observation) -> bool:
    if obs.agent is not Agent.COP:
        return False
    if obs.barriers_used >= obs.max_barriers or obs.own_pos in obs.barriers:
        return False
    blocked = obs.barriers | frozenset([obs.own_pos])
    rows, cols = obs.grid_size
    for action, delta in MOVE_DELTAS.items():
        if action is Action.STAY:
            continue
        candidate = (obs.own_pos[0] + delta[0], obs.own_pos[1] + delta[1])
        if (
            _in_bounds(candidate, rows, cols)
            and candidate not in blocked
            and candidate != obs.opp_estimate
        ):
            return True
    return False


def _cop_score(obs: Observation, action: Action) -> tuple[float, str]:
    est = obs.opp_estimate
    dist_now = _manhattan(obs.own_pos, est)
    if action is Action.PLACE_BARRIER:
        if not _can_place_barrier(obs):
            return (-999.0, "barrier illegal here")
        if dist_now == 0:
            return (120.0, "seal suspected thief cell")
        if dist_now == 1:
            return (95.0, "funnel adjacent suspect cell")
        if dist_now == 2 and obs.move_count >= 15:
            return (40.0, "late-game choke on estimate approach lane")
        return (-50.0, "barrier too far from estimate; chase instead")
    nxt = _target(obs, action)
    dist_next = _manhattan(nxt, est)
    if dist_next == 0:
        return (200.0, "capture attempt on estimate cell")
    gain = dist_now - dist_next
    mob = _mobility(nxt, obs)
    score = gain * 25.0 + mob * 0.5
    if action is Action.STAY:
        score -= 40.0
    reason = f"closes distance by {gain}" if gain > 0 else "holds or opens distance"
    if mob <= 2:
        score -= 5.0
        reason = f"{reason}; low mobility exit"
    return (score, reason)


def _thief_score(obs: Observation, action: Action) -> tuple[float, str]:
    return thief_apf_score(obs, action)


def score_action(obs: Observation, action: Action) -> float:
    """Return the tactical score for a single *action*."""
    if action is Action.PLACE_BARRIER and obs.agent is not Agent.COP:
        return -999.0
    scorer = _cop_score if obs.agent is Agent.COP else _thief_score
    return scorer(obs, action)[0]


def rank_actions(obs: Observation, *, top_n: int = 4) -> list[ActionHint]:
    """Return the top candidate actions for *obs* with scores and reasons."""
    scorer = _cop_score if obs.agent is Agent.COP else _thief_score
    actions = list(_legal_moves(obs))
    if obs.agent is Agent.COP and _can_place_barrier(obs):
        actions.append(Action.PLACE_BARRIER)
    hints = [ActionHint(action, *scorer(obs, action)) for action in actions]
    hints.sort(key=lambda item: item.score, reverse=True)
    return hints[:top_n]


def build_tactical_brief(obs: Observation) -> str:
    """Render a concise tactical snapshot for the LLM prompt."""
    est = obs.opp_estimate
    dist = _manhattan(obs.own_pos, est)
    rows, cols = obs.grid_size
    rounds_left = max(0, 25 - obs.move_count)
    barriers_left = obs.max_barriers - obs.barriers_used
    mob = _mobility(obs.own_pos, obs)
    ranked = rank_actions(obs)
    lines = [
        "Tactical snapshot (belief-based, not ground truth):",
        f"- Manhattan distance to opponent estimate: {dist}",
        f"- Your mobility (open neighbors): {mob}",
        f"- Known barriers on board: {len(obs.barriers)}",
        f"- Rounds remaining before thief escape win: {rounds_left}",
    ]
    if obs.agent is Agent.COP:
        lines.append(f"- Barriers remaining: {barriers_left}")
        if dist == 0:
            lines.append("- Priority: capture attempt — you are on the estimate cell.")
        elif dist == 1:
            lines.append("- Priority: close capture or seal the adjacent estimate cell.")
        elif rounds_left <= 8:
            lines.append("- Urgency high: cut off escape lanes toward open map edges.")
    else:
        belief_cells = len(build_belief_map(obs))
        u_here, u_cop, u_wall, u_mob = potential_at(obs.own_pos, obs)
        border_clear = _border_distance(obs.own_pos, rows, cols)
        lines.append(f"- Cop information-set cells (belief mass): {belief_cells}")
        lines.append(
            f"- Current potential U={u_here:.2f} "
            f"(cop={u_cop:.2f} wall={u_wall:.2f} mobility={u_mob:.2f})"
        )
        lines.append(f"- Border clearance: {border_clear}")
        lines.append(
            "- YOU MUST MOVE every turn unless completely surrounded (stay is illegal)."
        )
        lines.append(
            "- Engine will execute the minimax APF move; ranked hints show the math."
        )
        lines.append(
            "- Edges/corners are allowed only when every interior move has higher U "
            "(wall repulsion is weaker than cop threat)."
        )
        if dist <= 2:
            lines.append("- Threat high: favor mobility ≥5 and low U_cop.")
    lines.append("Ranked action hints (prefer top unless NL cues strongly disagree):")
    for idx, hint in enumerate(ranked, start=1):
        lines.append(f"  {idx}. {hint.action.value} — {hint.reason} (score {hint.score:.0f})")
    return "\n".join(lines)
