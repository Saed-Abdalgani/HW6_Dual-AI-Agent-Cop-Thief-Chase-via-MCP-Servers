"""Thief movement engine: information-set APF + one-step cop lookahead (maximin).

The thief MUST move when possible. Movement is chosen deterministically by this
module — LLM prompts are advisory only for NL taunts.

Traces: FR-LLM1, FR-NL2, T-P5-01.
"""

from __future__ import annotations

from cop_thief.constants import COP_ACTIONS, MOVE_DELTAS, Action
from cop_thief.services.orchestrator._types import Observation


def chebyshev(a: tuple[int, int], b: tuple[int, int]) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def _in_bounds(pos: tuple[int, int], rows: int, cols: int) -> bool:
    return 0 <= pos[0] < rows and 0 <= pos[1] < cols


def _target(obs: Observation, action: Action) -> tuple[int, int]:
    dr, dc = MOVE_DELTAS[action]
    r, c = obs.own_pos
    return (r + dr, c + dc)


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


def _border_clearance(pos: tuple[int, int], rows: int, cols: int) -> int:
    r, c = pos
    return min(r, rows - 1 - r, c, cols - 1 - c)


def build_belief_map(obs: Observation) -> dict[tuple[int, int], float]:
    """Normalized cop belief mass (information-set approximation)."""
    rows, cols = obs.grid_size
    est = obs.opp_estimate
    spread = max(1, min(3, 1 + obs.move_count // 6))
    raw: dict[tuple[int, int], float] = {}
    for r in range(rows):
        for c in range(cols):
            pos = (r, c)
            if pos == obs.own_pos or pos in obs.barriers:
                continue
            dist = chebyshev(pos, est)
            if dist <= spread:
                raw[pos] = 1.0 / ((1 + dist) ** 2)
    if not raw:
        raw[est] = 1.0
    total = sum(raw.values())
    return {pos: weight / total for pos, weight in raw.items()}


def _cop_repulsion(pos: tuple[int, int], belief: dict[tuple[int, int], float]) -> float:
    return sum(prob / (max(chebyshev(pos, cell), 1) ** 2) for cell, prob in belief.items())


def _wall_repulsion(pos: tuple[int, int], obs: Observation) -> float:
    rows, cols = obs.grid_size
    clearance = _border_clearance(pos, rows, cols)
    energy = 1.0 / (max(clearance, 1) ** 3)
    for barrier in obs.barriers:
        dist = chebyshev(pos, barrier)
        energy += 2.0 / (max(dist, 1) ** 3)
    return energy


def _mobility_potential(pos: tuple[int, int], obs: Observation) -> float:
    open_neighbors = _mobility(pos, obs)
    if open_neighbors == 0:
        return 15.0
    penalty = max(0, 5 - open_neighbors) * 0.5
    return (1.0 / open_neighbors) + penalty


def potential_at(pos: tuple[int, int], obs: Observation) -> tuple[float, float, float, float]:
    belief = build_belief_map(obs)
    u_cop = _cop_repulsion(pos, belief)
    u_wall = _wall_repulsion(pos, obs)
    u_mob = _mobility_potential(pos, obs)
    return (u_cop + u_wall + u_mob, u_cop, u_wall, u_mob)


def _legal_movement_actions(obs: Observation) -> list[Action]:
    rows, cols = obs.grid_size
    legal: list[Action] = []
    for action, (dr, dc) in MOVE_DELTAS.items():
        if action is Action.STAY:
            continue
        nxt = (obs.own_pos[0] + dr, obs.own_pos[1] + dc)
        if _in_bounds(nxt, rows, cols) and nxt not in obs.barriers:
            legal.append(action)
    return legal


def _simulate_cop_chase(cop_pos: tuple[int, int], thief_pos: tuple[int, int], obs: Observation) -> tuple[tuple[int, int], int]:
    """Greedy one-step cop pursuit toward *thief_pos* from *cop_pos*."""
    rows, cols = obs.grid_size
    best_pos = cop_pos
    best_dist = chebyshev(cop_pos, thief_pos)
    for action in COP_ACTIONS:
        if action is Action.PLACE_BARRIER:
            continue
        dr, dc = MOVE_DELTAS[action]
        nxt = (cop_pos[0] + dr, cop_pos[1] + dc)
        if not _in_bounds(nxt, rows, cols) or nxt in obs.barriers:
            continue
        dist = chebyshev(nxt, thief_pos)
        if dist < best_dist:
            best_dist = dist
            best_pos = nxt
    return best_pos, best_dist


def evaluate_thief_move(obs: Observation, action: Action) -> tuple[float, str]:
    """Maximin safety score for a thief move (higher = safer)."""
    if action is Action.STAY:
        if _legal_movement_actions(obs):
            return (-1_000_000.0, "must move — stay forbidden")
        u_total, u_cop, u_wall, u_mob = potential_at(obs.own_pos, obs)
        return (
            -u_total * 100.0,
            f"surrounded U={u_total:.2f}",
        )

    nxt = _target(obs, action)
    cop_pos = obs.opp_estimate
    cop_after, dist_after = _simulate_cop_chase(cop_pos, nxt, obs)
    dist_now = chebyshev(obs.own_pos, cop_pos)
    dist_land = chebyshev(nxt, cop_pos)

    if cop_after == nxt or dist_after == 0:
        return (-1_000_000.0, "cop captures after your move")

    u_total, u_cop, u_wall, u_mob = potential_at(nxt, obs)
    rows, cols = obs.grid_size
    clearance = _border_clearance(nxt, rows, cols)
    mob = _mobility(nxt, obs)

    score = (
        dist_after * 100.0
        + dist_land * 25.0
        + clearance * 18.0
        + mob * 8.0
        - u_total * 80.0
    )

    if dist_land < dist_now:
        score -= 80.0
    if dist_land <= 2:
        score -= 40.0
    if mob < 4:
        score -= 30.0
    if clearance == 0:
        score -= 25.0

    reason = (
        f"maximin dist_after={dist_after} U={u_total:.2f} "
        f"(cop={u_cop:.2f} wall={u_wall:.2f} mob={u_mob:.2f})"
    )
    return (score, reason)


def choose_thief_action(obs: Observation) -> Action:
    """Pick the thief move with maximum minimax safety score."""
    legal = _legal_movement_actions(obs)
    if not legal:
        return Action.STAY
    ranked = sorted(legal, key=lambda act: evaluate_thief_move(obs, act)[0], reverse=True)
    return ranked[0]


def thief_apf_score(obs: Observation, action: Action) -> tuple[float, str]:
    """Compatibility wrapper for ranked hints in LLM prompts."""
    return evaluate_thief_move(obs, action)
