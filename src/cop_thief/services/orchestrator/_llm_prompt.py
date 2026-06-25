"""LLM prompt construction with pursuit/evasion doctrine and tactical brief.

Traces: FR-LLM1, T-P3-03, T-P5-01.
"""

from __future__ import annotations

import json

from cop_thief.constants import Agent
from cop_thief.services.nlp.encoder import describe_position
from cop_thief.services.orchestrator._llm_tactics import build_tactical_brief
from cop_thief.services.orchestrator._types import Observation

_MOVE_ACTIONS = (
    "up",
    "down",
    "left",
    "right",
    "up_left",
    "up_right",
    "down_left",
    "down_right",
    "stay",
)
_COP_ACTIONS = (*_MOVE_ACTIONS, "place_barrier")

_COP_DOCTRINE = """\
Cop doctrine — partial-observation pursuit (POMDP-style centroid chase):

A. Belief handling
   - The opponent estimate region is your best belief of the thief centroid.
   - NL messages are noisy cues; never treat them as exact GPS.
   - When estimate and last message conflict, favor estimate unless message is very specific.

B. Primary objective
   - Capture: occupy the same cell as the thief before round 25.
   - Every turn ask: "Which action most reduces Manhattan distance to the estimate
     while preserving my mobility?"

C. Movement algorithm (apply mentally each turn)
   1. If a legal move lands on the estimate cell → choose it (capture attempt).
   2. Else pick among legal moves the one with lowest Manhattan distance to estimate.
   3. Tie-break toward moves that keep ≥3 open neighbors (avoid self-trapping).
   4. Avoid stay unless every move is blocked or distance already 0.

D. Barrier algorithm (place_barrier — cop only, budget is precious)
   Use a barrier when ANY of these holds:
   1. You are adjacent to the estimate (distance 1) and a barrier seals the suspect cell
      while you still have relocation — this creates a funnel.
   2. The thief estimate sits on a choke point (low mobility cell) and a barrier there
      collapses escape routes.
   3. Rounds are running out (≤8 left) and a barrier blocks the shortest escape vector
      toward the map edge even if not perfectly aligned.
   Do NOT barrier when:
   - Distance to estimate ≥2 (chase instead — barriers far from belief waste budget).
   - A direct closing move reduces distance this turn.
   - Barriers remaining = 0.

E. Anti-patterns (never do these)
   - Drifting away from the estimate without reason.
   - Using stay while legal closing moves exist.
   - Hoarding all 5 barriers until the game ends.
   - Ignoring ranked hints unless NL evidence is strong."""

_THIEF_DOCTRINE = """\
Thief doctrine — Information-Set Maximin via Artificial Potential Fields (APF):

OBJECTIVE: Survive 25 rounds. You win by NOT being captured — there is no exit cell.
You MUST MOVE every turn unless all 8 directions are blocked. Stay is illegal otherwise.

━━━ Step 1: Information-Set belief filter ━━━
Maintain a mental probability map M over cop cells (partial observability):
- Seed M around the opponent estimate region shown in the tactical brief.
- Each cop turn: expand possible cop cells by one Chebyshev step in all 8 directions.
- Survival filter: cop probability on YOUR cell is always zero (you were not captured).
- NL filter: opponent messages are noisy regional cues — narrow M when confident,
  widen when ambiguous. Never treat NL as exact coordinates.

━━━ Step 2: Artificial Potential Field (evaluate all 8 moves + stay) ━━━
For each candidate cell c, compute total potential U(c) — LOWER is SAFER:

  U(c) = U_cop(c) + U_wall(c) + U_mobility(c)

1) Cop repulsion U_cop(c) — expected threat from belief map M:
   U_cop(c) = Σ M(r,g) × 1 / D(c,(r,g))²
   where D is Chebyshev (8-directional) distance.

2) Wall/barrier repulsion U_wall(c) — cubic penalty near hazards:
   U_wall(c) = Σ_{walls,barriers} 1 / D(c,hazard)³
   Cubic exponent: ignore walls when far; spike when within 1–2 cells of border/barrier.
   This prevents corner suicide WITHOUT banning edges when cop pressure forces them.

3) Mobility degeneracy U_mobility(c) — counter the cop's 5 barriers:
   U_mobility(c) = 1 / open_neighbors(c)  (+ extra penalty if neighbors < 5)
   Prefer cells with many escape routes; avoid chokepoints a single barrier can seal.

━━━ Step 3: Maximin action selection ━━━
1. Drop illegal moves (out of bounds, into barriers).
2. DROP STAY if any legal move exists — you must move.
3. Compute U(c_next) for each remaining move.
4. Execute the MIN-U move (minimum total potential = maximum safety margin).
5. Edges/corners are acceptable ONLY when every interior candidate has higher U
   (cop repulsion dominates wall repulsion — better a border than cop-adjacent interior).

━━━ Why APF beats naive "run away" ━━━
- Pure distance maximization beelines into corners → cop barriers + wall = death.
- Cubic wall repulsion makes you orbit the center while repelling from cop belief mass.
- Mobility term keeps you out of narrow corridors one barrier can close.

━━━ Anti-patterns ━━━
- Staying put when movement exists (forbidden).
- Ignoring ranked APF hints unless NL strongly contradicts.
- Stepping toward cop estimate or into known barriers.
- Choosing a high-U move when a lower-U legal move exists."""


def build_llm_prompt(obs: Observation) -> str:
    """Build a decision prompt with doctrine, tactical brief, and exact actions."""
    allowed = list(_COP_ACTIONS if obs.agent is Agent.COP else _MOVE_ACTIONS)
    doctrine = _COP_DOCTRINE if obs.agent is Agent.COP else _THIEF_DOCTRINE
    schema = json.dumps({"action": allowed[0], "nl_message": "short taunt"})
    own_region = describe_position(obs.own_pos, obs.grid_size)
    opp_region = describe_position(obs.opp_estimate, obs.grid_size)
    brief = build_tactical_brief(obs)
    return (
        f"You are the {obs.agent.value} on a {obs.grid_size[0]}x{obs.grid_size[1]} grid.\n"
        f"Your region: {own_region}. Opponent estimate region: {opp_region}.\n"
        f"Round: {obs.move_count} of 25. Barriers used: {obs.barriers_used} of {obs.max_barriers}.\n"
        f"Last opponent message: {obs.last_message!r}.\n\n"
        f"{brief}\n\n"
        f"{doctrine}\n\n"
        "Decision contract:\n"
        "- Follow the ranked hints unless NL cues strongly contradict them.\n"
        + (
            "- THIEF: movement is computed by the minimax APF engine (not your choice); "
            "reply with the action shown in the taunt prompt.\n"
            if obs.agent is Agent.THIEF
            else ""
        )
        + "- action must be EXACTLY one allowed value below (no aliases).\n"
        "- nl_message: one short taunt, coarse regional hints only, no coordinates.\n\n"
        f"Allowed actions: {', '.join(allowed)}\n\n"
        f"Reply JSON only: {schema}"
    )
