# PRD — Game Engine Mechanism: Cop–Thief MCP System

| Field | Value |
|-------|-------|
| Document | Per-mechanism PRD — Game Engine |
| Project | `marl-cop-thief` |
| Version | 1.0 |
| Parent PRD | `docs/PRD.md` §7 |
| Implementation | `src/cop_thief/services/engine/` |
| Traces | FR-B*, FR-M*, FR-V*, FR-BR*, FR-S*, FR-L* |

---

## 1. Overview

The **Game Engine** is the authoritative source of truth for all game rules.
It is a pure, deterministic Python module with **no** external dependencies
on MCP servers, LLMs, or network calls. Given the same RNG seed it always
produces the same game trace.

---

## 2. Board State

### 2.1 Grid

- The board is an **N×M grid** of cells, where N (rows) and M (cols) come
  from `config.grid_size`. Default: **5×5**.
- Cells are indexed `(row, col)` with **row 0 = top**, **col 0 = left**.
- Valid cells satisfy `0 ≤ row < N` and `0 ≤ col < M`.

### 2.2 Agent Positions

- At any point the board holds exactly two agent positions:
  - **Cop** position: `(row_c, col_c)`
  - **Thief** position: `(row_t, col_t)`
- Neither agent may occupy the same cell as a **barrier**.
- At the **start** of a sub-game the positions are distinct and not on a barrier.

### 2.3 Barriers

- A **barrier** is a blocked cell. Once placed it persists for the rest of
  the sub-game.
- Barriers occupy a cell — **no agent may enter or occupy a barrier cell**.
- The board stores the set of barrier cells as `frozenset[tuple[int, int]]`.

---

## 3. Movement

### 3.1 Action Vocabulary

Each agent chooses one action per turn from the set defined in
`cop_thief.constants.Action`:

| Action | Δrow | Δcol |
|--------|------|------|
| `up` | −1 | 0 |
| `down` | +1 | 0 |
| `left` | 0 | −1 |
| `right` | 0 | +1 |
| `up_left` | −1 | −1 |
| `up_right` | −1 | +1 |
| `down_left` | +1 | −1 |
| `down_right` | +1 | +1 |
| `stay` | 0 | 0 |
| `place_barrier` | — | — |

### 3.2 Move Resolution

Given a current position `(r, c)` and action `a`:
1. Look up `(Δr, Δc)` from `MOVE_DELTAS[a]`.
2. Compute target `(r + Δr, c + Δc)`.
3. **Reject** the move if the target is outside the grid bounds.
4. **Reject** the move if the target cell is a barrier.
5. On rejection, the agent **stays in place** and the rejection is logged.

### 3.3 Out-of-Bounds Check

A cell `(r, c)` is **in-bounds** iff `0 ≤ r < rows` and `0 ≤ c < cols`.
Any move resulting in an out-of-bounds cell is illegal.

### 3.4 Barrier Crossing

Neither the cop nor the thief may enter a cell occupied by a barrier.
Diagonal moves do **not** bypass barriers — only the target cell is checked
(not intermediate cells).

---

## 4. Turn Order

- **Default:** Thief moves first, then Cop (controlled by `config.thief_moves_first = true`).
- **Alternative:** Cop first (`config.thief_moves_first = false`).
- One **round** = one thief move + one cop move.
- The move counter increments **once per round** (after both agents have moved).

---

## 5. Barriers

### 5.1 Placement

- Only the **cop** may place barriers via the `place_barrier` action.
- When the cop places a barrier:
  - The cop's **current cell** becomes a blocked barrier cell.
  - The cop is immediately relocated to the first legal adjacent cell in
    deterministic movement order, preserving the invariant that no agent
    occupies a barrier cell.
  - If no legal adjacent relocation is available, the action is rejected and
    no barrier is placed.
  - Placing a barrier on an already blocked cell is rejected and does not
    consume budget.
  - The barrier count for this sub-game is incremented.

### 5.2 Limits

- The cop may place at most `config.max_barriers` barriers per sub-game
  (default: **5**).
- A 6th `place_barrier` attempt is **rejected** (cop stays; rejection logged).
- The barrier counter resets to 0 at the start of each new sub-game.

### 5.3 Thief Restriction

- The thief **cannot** place barriers.
- A `place_barrier` action from the thief is always rejected.

---

## 6. Victory Conditions

### 6.1 Cop Wins (Capture)

- If, after any move, the cop's cell equals the thief's cell, the sub-game
  ends immediately with **cop win**.
- Capture is checked after **each individual agent move** within a round.

### 6.2 Thief Wins (Escape)

- If the sub-game reaches `config.max_moves` rounds **without capture**,
  the thief wins by escape.
- At move 25 (default) with no capture, outcome = **thief_win**.

---

## 7. Scoring

Points are awarded per sub-game according to `config.scoring`:

| Outcome | Cop points | Thief points |
|---------|-----------|--------------|
| Cop wins | `scoring.cop_win` (default 20) | `scoring.thief_loss` (default 5) |
| Thief wins | `scoring.cop_loss` (default 5) | `scoring.thief_win` (default 10) |

Totals are the cumulative sum across all **valid** sub-games.

---

## 8. Sub-Game Lifecycle

### 8.1 Single Sub-Game

1. Generate start positions (distinct, not on barriers, per `config.start_mode`).
2. Reset barriers counter to 0; barrier set to empty.
3. Run the turn loop until capture or `max_moves` exceeded.
4. Return a `SubGameResult` containing:
   - `winner`: `Outcome.COP_WIN` or `Outcome.THIEF_WIN`
   - `moves_used`: number of rounds played
   - `barriers_used`: number of barriers placed by cop
   - `cop_score`: points earned by cop
   - `thief_score`: points earned by thief

### 8.2 Full Game

1. Run sub-games until exactly **6 valid** sub-games have completed.
2. A **valid** sub-game is one that ends with a `COP_WIN` or `THIEF_WIN` outcome.
3. A sub-game ending in `TECHNICAL_FAILURE` is **not counted** and triggers an
   automatic **rerun** — the same slot is replayed.
4. Return a `FullGameResult` containing all 6 `SubGameResult` entries and
   cumulative `totals`.

---

## 9. Technical Failure

A sub-game is classified as `TECHNICAL_FAILURE` when:
- An unhandled exception occurs during the sub-game execution.
- The move loop exits without a valid terminal outcome.

Technical failures are logged, excluded from the 6-game count, and immediately
retried (no maximum retry limit — the game runs until 6 valid sub-games complete).

---

## 10. Determinism

When `config.seed` is set, the engine creates a `random.Random` instance
seeded with that value. This seed governs:
- Start-position randomisation.
- Any random tie-breaking in heuristic strategies.

**The same seed always produces an identical game trace.**

---

## 11. Invariants

These must hold at all times during a sub-game:

1. Both agent positions are in-bounds.
2. Neither agent occupies a barrier cell.
3. Barrier count ≤ `max_barriers`.
4. Move count ≤ `max_moves`.
5. Cop and thief start on distinct cells.

---

## 12. Engine Authority

The engine is the single source of truth for barrier legality, movement,
capture, scoring, and lifecycle state. MCP tools must route action requests
through `RuleEngine.apply_action()` and persist only the resulting engine state.

---

## 13. Edge Cases

| Case | Resolution |
|------|-----------|
| Agent tries to move off-grid | Rejected; agent stays; logged |
| Agent tries to move into barrier | Rejected; agent stays; logged |
| Thief tries `place_barrier` | Rejected; thief stays; logged |
| Cop tries 6th barrier | Rejected; cop stays; logged |
| Cop tries duplicate barrier | Rejected; budget unchanged; logged |
| Cop has no relocation after barrier | Rejected; no barrier placed; logged |
| Capture on thief's move | Sub-game ends immediately (cop wins) |
| Capture on cop's move | Sub-game ends immediately (cop wins) |
| `max_moves` reached exactly | Thief wins |

---

## 13. Module Map

```
src/cop_thief/services/engine/
├── __init__.py        # Public re-exports
├── board.py           # Board class: grid, agent positions, barriers, start positions
├── rules.py           # Move resolution, capture/escape detection, turn order
├── scoring.py         # Points calculation and totals accumulation
└── lifecycle.py       # SubGameResult, FullGameResult, sub-game & full-game runners
```
