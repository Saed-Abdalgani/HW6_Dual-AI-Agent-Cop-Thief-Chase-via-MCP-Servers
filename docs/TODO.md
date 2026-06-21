# TODO — Cop–Thief MCP System (Phased Execution Backlog)

| Field | Value |
|-------|-------|
| Document | Task backlog / execution checklist |
| Project | `marl-cop-thief` |
| Version | 1.0 (draft) |
| Source of truth | `docs/PRD.md`, `docs/PLAN.md` |
| Tooling | Python + `uv` only |

This backlog operationalizes the **9 phases (P0–P9)** defined in `PRD.md` §15 and `PLAN.md` §20.
Every task traces back to a PRD requirement (`FR-*`, `NFR-*`) and/or a PLAN component.

---

## How to Use This Document

### Status legend
- `[ ]` — Not started
- `[/]` — In progress
- `[x]` — Done
- `[-]` — Cancelled / dropped
- `[!]` — Blocked (see note)

### Priority legend
- **P0** — Blocker; nothing proceeds without it.
- **P1** — Critical for the assignment's core acceptance.
- **P2** — Important; required for full marks / robustness.
- **P3** — Nice-to-have / optional / bonus.

### Task ID convention
`T-<phase>-<nn>` — e.g., `T-P1-03` is task 3 of Phase 1. Sub-tasks use `.a/.b/.c`.

### Columns used per task block
- **ID** · **Priority** · **Status** · **Depends on** · **Traces to** (PRD/PLAN refs) · **DoD**

---

## Global Definition of Done (applies to EVERY task)

A task is **Done** only when ALL of the following hold:
- [ ] Code compiles and runs via `uv run` (no `pip`/`venv`/`python -m`).
- [ ] New/changed logic has unit and/or integration tests.
- [ ] `uv run ruff check .` reports **0** violations.
- [ ] `uv run pytest tests/` passes; global coverage stays **≥ 85%**.
- [ ] No hard-coded config values (board size, ports, URLs, timeouts, model names, secrets).
- [ ] No secrets committed; `.env` ignored; `.env-example` updated if new keys added.
- [ ] Each touched source file ≤ ~150 LOC; single responsibility respected.
- [ ] Public modules/classes/functions have docstrings.
- [ ] Relevant docs (`PRD`, `PLAN`, per-mechanism PRD, `README`) updated.
- [ ] Change traced to a PRD requirement ID in the commit/PR description.

---

## Milestone / Phase Overview

| Phase | Theme | Priority | Status | Exit criterion |
|-------|-------|----------|--------|----------------|
| P0 | Project scaffold + config + Gatekeeper | P0 | `[x]` | `uv sync` works; config validates; Ruff clean |
| P1 | Core game engine | P1 | `[x]` | Engine unit-tested, deterministic with seed |
| P2 | Two MCP servers (cop, thief) | P1 | `[ ]` | Tools callable w/ token; unauth rejected |
| P3 | Orchestrator + local E2E | P1 | `[ ]` | 6 sub-games run locally, 0 manual steps |
| P4 | Decision strategy | P1 | `[ ]` | Strategy selectable; baseline completes games |
| P5 | Natural-language messaging | P1 | `[ ]` | Free-text turns; ambiguity handled |
| P6 | GUI | P2 | `[ ]` | Visual run matches engine state |
| P7 | Cloud deploy + auth | P1 | `[ ]` | Public URLs live; revoke verified |
| P8 | Gmail JSON report | P1 | `[ ]` | JSON-only email after 6 valid sub-games |
| P9 | Hardening + README + audit | P1 | `[ ]` | All acceptance criteria green |

---

## Cross-Cutting Workstreams (run continuously across phases)

| Stream | Owner | Status | Notes |
|--------|-------|--------|-------|
| CC-SEC — Security & secrets hygiene | TBD | `[ ]` | Token auth, `.env`, no secret logging (NFR-1..3) |
| CC-CFG — Config-driven everything | TBD | `[ ]` | No hard-coding; schema kept in sync (FR-C*) |
| CC-TEST — Tests & coverage ≥85% | TBD | `[ ]` | Mocks for LLM/MCP/Gmail (NFR-8) |
| CC-LINT — Ruff zero violations | TBD | `[ ]` | Gate on every PR |
| CC-DOCS — Documentation upkeep | TBD | `[ ]` | PRD/PLAN/TODO/README/per-mechanism PRDs |
| CC-LOG — Structured logging | TBD | `[ ]` | Turn/message/tool/failure logs; redaction (NFR-10) |
| CC-OBS — Observability/metrics | TBD | `[ ]` | Latency/status counters via Gatekeeper |

---

## Pre-flight Decisions (resolve before/within P0)

These are the PRD §17 / PLAN §21 open questions. Capture answers here before deep implementation.

- [ ] **D-01 (P0)** — Confirm `group_name`, `students[]`, `github_repo`. _Traces:_ FR-E5, report contract.
- [x] **D-02 (P0)** — Choose LLM path: cloud API (Option 1) vs hybrid Ollama (Option 3). _Decision: cloud API default; provider/model from config (pluggable)._ _Traces:_ FR-LLM1/2.
- [ ] **D-03 (P0)** — Choose cloud platform (Prefect Cloud vs alternative). _Traces:_ G6, PLAN §15.2. _(deferred to P7)_
- [ ] **D-04 (P0)** — Choose Gmail auth (OAuth / service account / app-password). _Traces:_ FR-E3. _(deferred to P8)_
- [x] **D-05 (P0)** — Choose config format (`config.yaml` vs `config.json`). _Decision: YAML._ _Traces:_ FR-C1.
- [ ] **D-06 (P1)** — Decide GUI framework (Pygame / Tkinter / Streamlit). _Traces:_ FR-G1.
- [ ] **D-07 (P3)** — Decide whether to implement Q-learning. _Traces:_ FR-D2.

---

## Phase P0 — Project Scaffold, Config & Gatekeeper

**Goal:** Establish the `uv`-managed project skeleton, configuration loading, secrets handling, the
central API Gatekeeper shell, and CI quality gates so every later phase inherits the standards.

**Priority:** P0 · **Status:** `[x]` · **Traces:** PLAN §1, §5, §8; PRD §10, §11, NFR-5..9.

### Tooling & repository setup
- [x] **T-P0-01 (P0)** — Initialize `uv` project (`pyproject.toml`, `uv.lock`).
  - DoD: `uv sync` succeeds on a clean checkout; Python version pinned.
- [x] **T-P0-02 (P0)** — Create the full directory tree from `PLAN.md` §5.
  - Sub: `src/cop_thief/{sdk,services,shared,mcp_servers,gui,cli}`, `tests/{unit,integration}`,
    `docs/`, `config/`, `data/`, `results/`, `assets/`, `notebooks/`.
  - DoD: All packages have `__init__.py`; tree matches PLAN exactly.
- [x] **T-P0-03 (P0)** — Add `.gitignore` (ignore `.env`, `*.key`, `*.pem`, caches, `data/`, secrets).
  - DoD: `git status` never shows secret files. _Traces:_ NFR-2, Security.
- [x] **T-P0-04 (P0)** — Create `.env-example` listing all required env var **names** (no values).
  - Sub: `LLM_API_KEY`, `MCP_COP_TOKEN`, `MCP_THIEF_TOKEN`, `GMAIL_*`. _Traces:_ FR-C3.
- [x] **T-P0-05 (P1)** — Configure Ruff in `pyproject.toml` (line length, rules).
  - DoD: `uv run ruff check .` runs and is clean on the skeleton.
- [x] **T-P0-06 (P1)** — Configure pytest + coverage in `pyproject.toml` (fail under 85%).
  - DoD: `uv run pytest` runs; coverage threshold wired.
- [x] **T-P0-07 (P2)** — Add CI workflow (lint + test + coverage gate).
  - DoD: CI fails on Ruff violations or coverage < 85%.

### Configuration subsystem (`shared/config.py`)
- [x] **T-P0-08 (P0)** — Implement `Config` loader for the chosen format (D-05).
  - DoD: Loads `config/config.yaml` (or json); returns typed object. _Traces:_ FR-C1.
- [x] **T-P0-09 (P0)** — Define the authoritative config schema with all PRD §11 keys + defaults.
  - Sub: `grid_size`, `max_moves`, `num_games`, `max_barriers`, `scoring.*`, `start_mode`,
    `thief_moves_first`, `discount_gamma`, `strategy`, `llm.*`, `mcp.*`, `gatekeeper.*`,
    `email.to`, `timezone`, `seed`. _Traces:_ FR-C2, PLAN §10.1.
- [x] **T-P0-10 (P1)** — Validate config (types, ranges, required keys) with clear errors.
  - DoD: Invalid config raises actionable error; tested. _Traces:_ NFR (input validation).
- [x] **T-P0-11 (P1)** — Load secrets strictly from env vars (never from config files).
  - DoD: Missing required secret fails fast with safe message. _Traces:_ FR-C3, Security.
- [x] **T-P0-12 (P1)** — Create a sample `config/config.yaml` with documented defaults.
  - DoD: Matches schema; comments explain each key.

### Constants & version
- [x] **T-P0-13 (P2)** — Implement `constants.py` (action vocabulary, agent names, enums).
  - Sub: actions `up,down,left,right,up_left,up_right,down_left,down_right,stay,place_barrier`.
  - DoD: No magic strings elsewhere reference these literals. _Traces:_ PLAN §9.
- [x] **T-P0-14 (P3)** — Implement `shared/version.py` (single source of version).

### API Gatekeeper shell (`shared/gatekeeper.py`)
- [x] **T-P0-15 (P1)** — Define `Gatekeeper` class + `OutboundRequest`/`Response` types.
  - DoD: Interface matches PLAN §8; no provider specifics leak in. _Traces:_ NFR-5.
- [x] **T-P0-16 (P1)** — Implement rate limiting (token-bucket per target) from config.
  - DoD: Exceeding rate is throttled, not dropped; tested. _Traces:_ `gatekeeper.rate_limit_*`.
- [x] **T-P0-17 (P1)** — Implement retries with exponential backoff + jitter (max from config).
  - DoD: Transient failures retried up to limit; tested with mock.
- [x] **T-P0-18 (P1)** — Implement bounded queue + backpressure (queue size from config).
  - DoD: Saturation handled deterministically; tested.
- [x] **T-P0-19 (P1)** — Implement per-call timeout from config.
- [x] **T-P0-20 (P1)** — Implement structured logging with **secret redaction**.
  - DoD: Tokens/keys never appear in logs; verified by test. _Traces:_ NFR-10, Security.

### Logging & auth scaffolding
- [x] **T-P0-21 (P2)** — Implement `shared/logging.py` (structured logger factory).
- [x] **T-P0-22 (P1)** — Implement `shared/auth.py` skeleton: issue/verify/revoke token API.
  - DoD: Tokens hashed at rest; verify/revoke unit-tested. _Traces:_ NFR-1/2, PLAN §16.

### Phase P0 tests
- [x] **T-P0-23 (P1)** — Unit tests: config load/validate (happy + invalid + missing secret).
- [x] **T-P0-24 (P1)** — Unit tests: Gatekeeper rate-limit, retry, timeout, backpressure (mocked).
- [x] **T-P0-25 (P1)** — Unit tests: auth issue/verify/revoke; log redaction.

### Phase P0 Definition of Done (exit criteria)
- [x] `uv sync` works from clean clone; structure matches PLAN §5.
- [x] Config loads + validates; secrets only from env; sample config present.
- [x] Gatekeeper shell functional (rate/retry/queue/timeout/redaction) and tested.
- [x] Ruff clean; coverage ≥ 85% on implemented modules; CI gate active.

---

## Phase P1 — Core Game Engine

**Goal:** Implement deterministic, fully tested game rules (board, movement, capture, barriers,
scoring, sub-game/full-game lifecycle) independent of MCP/LLM. This is the rules authority.

**Priority:** P1 · **Status:** `[ ]` · **Traces:** PRD §7 (FR-B*, FR-M*, FR-V*, FR-BR*, FR-S*, FR-L*),
PLAN §6, `docs/PRD_game_engine.md`.

### Per-mechanism PRD
- [x] **T-P1-01 (P1)** — Write `docs/PRD_game_engine.md` (state, transitions, edge cases, invariants).
  - DoD: Documents capture rule, barrier crossing, turn order, max-moves termination.

### Board (`services/engine/board.py`)
- [x] **T-P1-02 (P1)** — Implement `Board` from `grid_size` config (no hard-coded size).
  - DoD: Supports 5×5 default and arbitrary sizes; tested 5×5 and 7×7. _Traces:_ FR-B1/B2, AC-5.
- [x] **T-P1-03 (P1)** — Implement cell coordinates + in-bounds check.
  - DoD: Out-of-bounds detection unit-tested. _Traces:_ FR-M3.
- [x] **T-P1-04 (P1)** — Implement barrier storage + `is_blocked(cell)`.
  - DoD: Blocked cells tracked; tested. _Traces:_ FR-BR3.
- [x] **T-P1-05 (P1)** — Implement start-position generator (`random` | `strategy`) from config.
  - DoD: Start cells distinct, not on barrier; deterministic under `seed`. _Traces:_ FR-B3/B4, NFR-11.

### Movement & legality (`services/engine/rules.py`)
- [x] **T-P1-06 (P1)** — Implement 8-direction + `stay` move resolution.
  - DoD: All diagonal/orthogonal moves produce correct target cells. _Traces:_ FR-M1/M2.
- [x] **T-P1-07 (P1)** — Reject moves leaving the board.
  - DoD: Illegal off-board move rejected; tested. _Traces:_ FR-M3.
- [x] **T-P1-08 (P1)** — Reject moving into/crossing a blocked square (both players).
  - DoD: Barrier-crossing rejected; tested for cop and thief. _Traces:_ FR-M4, FR-BR3.
- [x] **T-P1-09 (P1)** — Enforce turn order (thief first by default, configurable).
  - DoD: Turn sequence correct; tested both orderings. _Traces:_ FR-M5, `thief_moves_first`.

### Barriers
- [x] **T-P1-10 (P1)** — Implement cop `place_barrier` (occupies current cell, no move that turn).
  - DoD: Position unchanged; cell becomes blocked; tested. _Traces:_ FR-BR1/BR2.
- [x] **T-P1-11 (P1)** — Enforce `max_barriers` (default 5) per sub-game.
  - DoD: 6th barrier rejected; counter resets per sub-game; tested. _Traces:_ FR-BR4, AC-4.
- [x] **T-P1-12 (P1)** — Forbid thief from placing barriers.
  - DoD: Thief barrier attempt rejected; tested. _Traces:_ FR-BR5.

### Victory & scoring
- [x] **T-P1-13 (P1)** — Implement capture detection (cop cell == thief cell ⇒ cop wins).
  - DoD: Capture ends sub-game with cop win; tested. _Traces:_ FR-V1.
- [x] **T-P1-14 (P1)** — Implement thief-escape detection (survive `max_moves` ⇒ thief wins).
  - DoD: At move 25 with no capture, thief wins; tested. _Traces:_ FR-V2/V3, AC-4.
- [x] **T-P1-15 (P1)** — Implement scoring (`scoring.py`) from config table.
  - DoD: Cop-win → 20/5; thief-win → 5/10; values from config; tested. _Traces:_ FR-S1, PLAN §10.4.
- [x] **T-P1-16 (P1)** — Implement totals accumulation across sub-games.
  - DoD: Totals sum correctly; max 90 / min 30 bounds documented. _Traces:_ FR-S2/S3.

### Lifecycle (`services/engine/lifecycle.py`)
- [x] **T-P1-17 (P1)** — Implement single sub-game runner (≤ 25 moves, returns result).
  - DoD: Produces `SubGameResult` (winner, moves, barriers_used, scores). _Traces:_ FR-L1, PLAN §10.4.
- [x] **T-P1-18 (P1)** — Implement full-game runner: loop until **6 valid** sub-games.
  - DoD: Exactly 6 valid results collected. _Traces:_ FR-L2, AC-3.
- [x] **T-P1-19 (P1)** — Implement technical-failure detection + **rerun** (invalid not counted).
  - DoD: Forced failure triggers rerun; invalid excluded; tested. _Traces:_ FR-L3, NFR-4.

### Phase P1 tests
- [x] **T-P1-20 (P1)** — Unit tests: board bounds, diagonal/orth moves, start generation.
- [x] **T-P1-21 (P1)** — Unit tests: barrier crossing, barrier limit, thief-barrier rejection.
- [x] **T-P1-22 (P1)** — Unit tests: capture, max-moves escape, turn order.
- [x] **T-P1-23 (P1)** — Unit tests: scoring table + totals (both outcomes).
- [x] **T-P1-24 (P1)** — Unit tests: lifecycle 6-valid loop + forced rerun on technical failure.
- [x] **T-P1-25 (P1)** — Determinism test: same `seed` ⇒ identical game trace. _Traces:_ NFR-11.

### Phase P1 Definition of Done (exit criteria)
- [x] Engine fully implements PRD §7 rules; pure and deterministic with `seed`.
- [x] All engine unit tests pass; engine coverage ≥ 85%.
- [x] `docs/PRD_game_engine.md` complete and consistent with code.
- [x] Ruff clean; files ≤ ~150 LOC.

---

## Phase P2 — Two MCP Servers (Cop & Thief)

**Goal:** Build two **independent** MCP servers that expose **tools only** (no LLM inside), with
token authentication and input validation, runnable locally on distinct ports.

**Priority:** P1 · **Status:** `[x]` · **Traces:** PRD §8.1 (FR-MCP1..5), PLAN §9, §16, NFR-1/2.

### Shared tool layer (`mcp_servers/tools.py`)
- [x] **T-P2-01 (P1)** — Implement `send_message(from, text)` tool → stores NL message for opponent.
  - DoD: Returns `{ok, msg_id}`; message persisted/queued. _Traces:_ FR-MCP3, FR-NL4, PLAN §10.2.
- [x] **T-P2-02 (P1)** — Implement `receive_message(for_agent)` → latest NL message.
  - DoD: Returns `{text, msg_id}` or empty; tested. _Traces:_ FR-MCP3.
- [x] **T-P2-03 (P1)** — Implement `update_position(agent, pos)` (engine-authoritative write).
  - DoD: Rejects out-of-bounds/blocked; returns `{ok, pos}`. _Traces:_ FR-MCP3, FR-MCP4.
- [x] **T-P2-04 (P1)** — Implement `verify_position(agent)` → `{pos}`.
- [x] **T-P2-05 (P1)** — Implement `choose_action(agent, observation)` → `{action}`.
  - DoD: Returns a legal action token; LLM NOT called here. _Traces:_ FR-MCP2, PLAN §9.
- [x] **T-P2-06 (P1)** — Implement `apply_action(agent, action)` → `{state_delta, legal}` via engine.
  - DoD: Illegal actions rejected with reason; tested. _Traces:_ FR-MCP4.
- [x] **T-P2-07 (P1)** — Implement `game_status()` → `{move_count, scores, over, winner}`.
- [x] **T-P2-08 (P1)** — Input validation for every tool (bounds, turn ownership, barrier budget).
  - DoD: Malformed inputs return structured errors; tested. _Traces:_ FR-MCP4, Security.

### Cop server (`mcp_servers/cop_server.py`)
- [x] **T-P2-09 (P1)** — Wire cop server exposing the tool set on `mcp.cop_url` port from config.
  - DoD: Server starts on configured port; no hard-coded port. _Traces:_ FR-MCP1/5, FR-C1.
- [x] **T-P2-10 (P1)** — Cop-only capability: expose `place_barrier` action path.
  - DoD: Cop can request barrier; thief cannot. _Traces:_ FR-BR1, FR-BR5.

### Thief server (`mcp_servers/thief_server.py`)
- [x] **T-P2-11 (P1)** — Wire thief server exposing the tool set on `mcp.thief_url` port from config.
  - DoD: Independent process from cop server; distinct port. _Traces:_ FR-MCP1/5.
- [x] **T-P2-12 (P1)** — Ensure thief server rejects `place_barrier`.
  - DoD: Tested rejection. _Traces:_ FR-BR5.

### Authentication & security
- [x] **T-P2-13 (P1)** — Enforce token auth on every tool call (verify via `shared/auth.py`).
  - DoD: Missing/invalid token ⇒ rejected (401-equivalent); tested. _Traces:_ NFR-1, AC-7.
- [x] **T-P2-14 (P1)** — Support token revocation (revoked token rejected immediately).
  - DoD: Revoke then call ⇒ rejected; tested. _Traces:_ NFR-2, AC-7.
- [x] **T-P2-15 (P1)** — Route all server-side egress (if any) and logging through Gatekeeper/redaction.
  - DoD: No token/secret in server logs. _Traces:_ NFR-10.

### Phase P2 tests
- [x] **T-P2-16 (P1)** — Unit tests: each tool happy-path + invalid-input + auth-failure.
- [x] **T-P2-17 (P1)** — Integration test: start both servers locally; call tools with token.
- [x] **T-P2-18 (P1)** — Security test: unauth + revoked-token calls rejected on both servers.

### Phase P2 Definition of Done (exit criteria)
- [x] Two independent servers run locally on distinct configured ports.
- [x] All tools callable with a valid token; no LLM inside servers.
- [x] Unauthenticated and revoked-token calls are rejected (verified).
- [x] Ruff clean; coverage ≥ 85% on server/tool modules.

---

## Phase P3 — Orchestrator & Local End-to-End

**Goal:** Build the MCP-client orchestrator that drives the turn loop, calls the (mockable) LLM,
invokes MCP tools, validates actions, and runs **6 valid sub-games locally with zero manual steps**.

**Priority:** P1 · **Status:** `[ ]` · **Traces:** PRD §8.2 (FR-O1..4), PLAN §4, §11, §12, NFR-4.

### MCP client (`orchestrator/mcp_client.py`)
- [ ] **T-P3-01 (P1)** — Implement `McpClient` wrapping cop & thief tool calls via Gatekeeper + token.
  - DoD: All MCP calls go through Gatekeeper; tokens injected from env. _Traces:_ FR-O2, NFR-5.
- [ ] **T-P3-02 (P1)** — Implement health check (both servers reachable) for SDK `health_check()`.
  - DoD: Returns reachability status; tested with mocks. _Traces:_ PLAN §7.

### LLM client (`orchestrator/llm_client.py`)
- [ ] **T-P3-03 (P1)** — Implement provider-agnostic `LlmClient` via Gatekeeper (provider/model/timeout from config).
  - DoD: Pluggable provider; key from env; mockable in tests. _Traces:_ FR-LLM1/2/4, PLAN §13.
- [ ] **T-P3-04 (P1)** — Define LLM output contract `{action, nl_message}` + JSON parse.
  - DoD: Valid JSON parsed; malformed handled. _Traces:_ ADR-6, PLAN §13.
- [ ] **T-P3-05 (P1)** — Implement fallback to heuristic strategy on parse/legality failure.
  - DoD: Vague/invalid LLM output never stalls a turn; tested. _Traces:_ Risk mitigation, FR-NL3.

### Turn controller (`orchestrator/turn_controller.py`)
- [ ] **T-P3-06 (P1)** — Implement per-turn flow: context → LLM decision → MCP send → apply_action.
  - DoD: Matches PLAN §11 sequence; tested with mocks. _Traces:_ FR-O3.
- [ ] **T-P3-07 (P1)** — Enforce turn order (thief first) and alternate correctly.
  - DoD: Order verified across a multi-turn sub-game. _Traces:_ FR-M5.
- [ ] **T-P3-08 (P1)** — Implement `ActionValidator` (reject illegal moves/barriers before apply).
  - DoD: Illegal action requests blocked client-side; tested. _Traces:_ PLAN §4, FR-MCP4.

### Game loop & results (`orchestrator/game_loop.py`)
- [ ] **T-P3-09 (P1)** — Implement sub-game driver using engine + MCP + LLM.
  - DoD: Completes a sub-game ≤ 25 moves end-to-end (mocked LLM). _Traces:_ FR-L1.
- [ ] **T-P3-10 (P1)** — Implement full-game driver: loop to **6 valid** sub-games, auto-rerun failures.
  - DoD: 6 valid sub-games, 0 manual steps; forced failure rerun tested. _Traces:_ FR-L2/L3, AC-2/3.
- [ ] **T-P3-11 (P1)** — Implement `ResultCollector` accumulating per-sub-game results + totals.
  - DoD: Totals match scoring; structure matches PLAN §10.4. _Traces:_ FR-S2.

### Opponent estimator (`orchestrator/estimator.py`)
- [ ] **T-P3-12 (P2)** — Implement belief/estimate of opponent position from history (pre-NL stub).
  - DoD: Provides estimate to strategy; refined in P5. _Traces:_ FR-NL2, PLAN §14.

### SDK & CLI wiring
- [ ] **T-P3-13 (P1)** — Implement `sdk/facade.py` (`run_sub_game`, `run_full_game`, `get_state`, `health_check`).
  - DoD: Single public entry; GUI/CLI use only this. _Traces:_ NFR-7, PLAN §7.
- [ ] **T-P3-14 (P1)** — Implement `cli/main.py` single-command autonomous run via SDK.
  - DoD: One command runs full game to completion. _Traces:_ AC-2.

### Phase P3 tests
- [ ] **T-P3-15 (P1)** — Integration: full 6-valid-sub-game loop with mocked MCP + mocked LLM.
- [ ] **T-P3-16 (P1)** — Integration: forced technical-failure → rerun → still 6 valid. _Traces:_ FR-L3.
- [ ] **T-P3-17 (P1)** — Unit: LLM JSON parse + heuristic fallback path.
- [ ] **T-P3-18 (P1)** — Unit: ActionValidator rejects illegal moves/barriers.

### Phase P3 Definition of Done (exit criteria)
- [ ] One command runs a full autonomous game locally (0 manual steps).
- [ ] Exactly 6 valid sub-games; technical failures auto-rerun and excluded.
- [ ] All external calls (LLM, MCP) routed through Gatekeeper.
- [ ] Ruff clean; coverage ≥ 85%.

---

## Phase P4 — Decision Strategy

**Goal:** Provide selectable decision strategies — a mandatory heuristic baseline, optional tabular
Q-learning, and an LLM strategy — chosen via config and feeding off the opponent estimate.

**Priority:** P1 · **Status:** `[ ]` · **Traces:** PRD §8.5 (FR-D1..3), PLAN §14, `docs/PRD_qlearning.md`.

### Strategy interface (`services/strategy/base.py`)
- [ ] **T-P4-01 (P1)** — Define `Strategy` interface: `choose(observation) -> action`.
  - DoD: All strategies implement it; selectable by `strategy` config. _Traces:_ FR-D3, ADR-5.
- [ ] **T-P4-02 (P1)** — Implement strategy factory keyed by config (`heuristic|qlearning|llm`).
  - DoD: Unknown value ⇒ clear error; default `heuristic`. _Traces:_ FR-D3.

### Heuristic baseline (`services/strategy/heuristic.py`)
- [ ] **T-P4-03 (P1)** — Implement Manhattan-distance policy: cop minimizes, thief maximizes distance.
  - DoD: Cop closes in; thief flees; respects legality. _Traces:_ FR-D1, PLAN §14.
- [ ] **T-P4-04 (P1)** — Implement cop barrier heuristic (place when adjacent & budget remains).
  - DoD: Uses ≤ 5 barriers sensibly; tested. _Traces:_ FR-BR4.
- [ ] **T-P4-05 (P1)** — Integrate opponent estimate (from `estimator.py`) into distance calc.
  - DoD: Uses belief, not ground-truth opponent coords. _Traces:_ FR-NL2, partial observability.

### Optional Q-learning (`services/strategy/qlearning.py`)
- [ ] **T-P4-06 (P3)** — Write `docs/PRD_qlearning.md` (state encoding, actions, reward, α/γ, update).
  - DoD: Documents Bellman update `Q←Q+α[r+γ·maxQ(s',a')−Q]`. _Traces:_ PRD §14, FR-D2.
- [ ] **T-P4-07 (P3)** — Implement state encoding `(own_pos, opp_estimate, barriers)`.
- [ ] **T-P4-08 (P3)** — Implement Q-table + Bellman update with α, γ from config.
  - DoD: Update math unit-tested on a tiny grid. _Traces:_ PRD §14.
- [ ] **T-P4-09 (P3)** — Implement training loop + Q-table persistence (save/load to `data/`).
- [ ] **T-P4-10 (P3)** — Produce learning-curve plot to `assets/` for README evidence.
  - DoD: Curve generated; referenced in README §evidence. _Traces:_ README §3.

### LLM strategy (`services/strategy/llm_strategy.py`)
- [ ] **T-P4-11 (P2)** — Implement prompt-based strategy returning `{action, nl_message}`.
  - DoD: Uses `LlmClient`; validates action legality. _Traces:_ ADR-6, PLAN §13.

### Phase P4 tests
- [ ] **T-P4-12 (P1)** — Unit: heuristic cop reduces distance; thief increases it (mock state).
- [ ] **T-P4-13 (P1)** — Unit: barrier heuristic respects limit and legality.
- [ ] **T-P4-14 (P1)** — Unit: strategy factory selects correct class from config.
- [ ] **T-P4-15 (P3)** — Unit: Q-learning Bellman update produces expected values.

### Phase P4 Definition of Done (exit criteria)
- [ ] Heuristic baseline plays full games to completion via the orchestrator.
- [ ] Strategy is selectable purely via config (no code change).
- [ ] Strategies consume the opponent **estimate**, not ground truth.
- [ ] Ruff clean; coverage ≥ 85% (optional Q-learning excluded if not implemented).

---

## Phase P5 — Natural-Language Messaging

**Goal:** Replace rigid signaling with **free-text** inter-agent messages; agents encode intent in
natural language, parse incoming messages, and update opponent estimates under ambiguity.

**Priority:** P1 · **Status:** `[ ]` · **Traces:** PRD §8.3 (FR-NL1..4), PLAN §13, §14,
`docs/PRD_nl_protocol.md`.

### Per-mechanism PRD
- [ ] **T-P5-01 (P1)** — Write `docs/PRD_nl_protocol.md` (message style, intents, ambiguity policy).
  - DoD: Defines that raw coordinate transfer is forbidden; gives examples. _Traces:_ FR-NL1, ADR-6.

### Encoder (`services/nlp/encoder.py`)
- [ ] **T-P5-02 (P1)** — Implement state→NL message generation (taunts/hints/bluffs), not raw coords.
  - DoD: Output is natural language; no literal `(r,c)` of self. _Traces:_ FR-NL1.
- [ ] **T-P5-03 (P2)** — Support deception/partial-truth styles (configurable tone).
  - DoD: Thief can mislead; cop can probe; documented. _Traces:_ PRD §2, challenges.

### Parser & estimator (`services/nlp/parser.py`, `orchestrator/estimator.py`)
- [ ] **T-P5-04 (P1)** — Implement NL message parsing → intent + region/direction cues.
  - DoD: Extracts coarse cues from free text; tested on samples. _Traces:_ FR-NL2.
- [ ] **T-P5-05 (P1)** — Upgrade `OpponentEstimator` to fuse NL cues + move history into a belief.
  - DoD: Belief updates over turns; uncertainty represented. _Traces:_ FR-NL2, partial observability.
- [ ] **T-P5-06 (P1)** — Handle ambiguity/misunderstanding gracefully (no crash, sane default).
  - DoD: Garbled/empty message ⇒ estimate unchanged + heuristic fallback. _Traces:_ FR-NL3.

### Integration
- [ ] **T-P5-07 (P1)** — Route all turn messages through MCP `send_message`/`receive_message`.
  - DoD: Every turn exchanges an NL message via MCP; visible in logs. _Traces:_ FR-NL4, AC-6.
- [ ] **T-P5-08 (P2)** — Log NL transcript per sub-game to `results/` for evidence.
  - DoD: Transcript saved; referenced by README. _Traces:_ README §3, CC-LOG.

### Phase P5 tests
- [ ] **T-P5-09 (P1)** — Unit: encoder produces NL (no raw self-coords) for varied states.
- [ ] **T-P5-10 (P1)** — Unit: parser extracts expected cues from sample messages.
- [ ] **T-P5-11 (P1)** — Unit: estimator updates belief from NL + history.
- [ ] **T-P5-12 (P1)** — Robustness: ambiguous/empty message handled without failure.
- [ ] **T-P5-13 (P1)** — Integration: full sub-game where turns use NL via MCP.

### Phase P5 Definition of Done (exit criteria)
- [ ] 100% of inter-agent turns exchange natural-language messages via MCP (AC-6).
- [ ] No reliance on direct numeric coordinate transfer.
- [ ] Ambiguity/misunderstanding handled gracefully with fallback.
- [ ] `docs/PRD_nl_protocol.md` complete; NL transcript logged.
- [ ] Ruff clean; coverage ≥ 85%.

---

## Phase P6 — Graphical User Interface

**Goal:** Provide a GUI (SDK-only consumer) that visualizes the grid, both agents, barriers,
movement over time, and current scores — used as evidence the system works.

**Priority:** P2 · **Status:** `[ ]` · **Traces:** PRD §8.7 (FR-G1..3), PLAN §6, NFR-7, UI/UX rules.

- [ ] **T-P6-01 (P2)** — Choose & scaffold GUI framework per D-06 (`gui/app.py`).
  - DoD: App launches; imports only `CopThiefSDK`. _Traces:_ FR-G3, NFR-7.
- [ ] **T-P6-02 (P2)** — Render the grid sized from config (no hard-coded size).
  - DoD: 5×5 and 7×7 render correctly. _Traces:_ FR-G1, AC-5.
- [ ] **T-P6-03 (P2)** — Render cop, thief, and barrier cells distinctly.
  - DoD: Positions match `SDK.get_state()`. _Traces:_ FR-G1.
- [ ] **T-P6-04 (P2)** — Animate/step movement over time across a sub-game.
  - DoD: Frames follow engine state per turn. _Traces:_ FR-G2.
- [ ] **T-P6-05 (P2)** — Display current scores and sub-game index.
  - DoD: Scores update after each sub-game. _Traces:_ FR-G2.
- [ ] **T-P6-06 (P3)** — Show latest NL message exchanged (transcript panel).
  - DoD: Optional panel reflects last messages. _Traces:_ README evidence.
- [ ] **T-P6-07 (P2)** — Apply Nielsen heuristics: clear status, error states, minimal design.
  - DoD: Loading/error/finished states visible. _Traces:_ UI/UX rules.
- [ ] **T-P6-08 (P2)** — Capture GUI screenshots into `assets/` for README evidence.
  - DoD: Screenshots saved + referenced. _Traces:_ README §3.

### Phase P6 tests
- [ ] **T-P6-09 (P2)** — Test GUI state-mapping logic (pure functions) without rendering.
- [ ] **T-P6-10 (P3)** — Smoke test: GUI launches and renders one frame headlessly if feasible.

### Phase P6 Definition of Done (exit criteria)
- [ ] GUI shows grid, cop, thief, barriers, movement, and scores.
- [ ] GUI calls SDK only (no engine/orchestrator imports).
- [ ] Screenshots captured for README; Ruff clean; coverage ≥ 85% on testable GUI logic.

---

## Phase P7 — Cloud Deployment & Authentication

**Goal:** Deploy both MCP servers to a public platform with token auth and revocation, producing the
two public URLs, using the hybrid architecture so the local machine/Ollama is never exposed.

**Priority:** P1 · **Status:** `[ ]` · **Traces:** PRD §8.1 (FR-MCP5), §9 (NFR-1/2/3), PLAN §15, §16.

### Deployment
- [ ] **T-P7-01 (P1)** — Prepare deployment artifacts/config for chosen platform (D-03).
  - DoD: Reproducible deploy steps documented. _Traces:_ G6, PLAN §15.2.
- [ ] **T-P7-02 (P1)** — Deploy **Cop MCP server** → obtain public `cop_mcp_url`.
  - DoD: URL reachable over HTTPS with token. _Traces:_ FR-MCP5.
- [ ] **T-P7-03 (P1)** — Deploy **Thief MCP server** → obtain public `thief_mcp_url`.
  - DoD: URL reachable over HTTPS with token. _Traces:_ FR-MCP5.
- [ ] **T-P7-04 (P1)** — Update config with cloud URLs (kept out of secrets; tokens in env).
  - DoD: Orchestrator runs against cloud URLs. _Traces:_ FR-C1.

### Hybrid architecture & security hardening
- [ ] **T-P7-05 (P1)** — Verify hybrid mode: LLM/Ollama local, client outbound HTTPS only.
  - DoD: No inbound exposure of local machine; Ollama 11434 never published. _Traces:_ NFR-3, ADR-4.
- [ ] **T-P7-06 (P1)** — Enforce token auth on cloud endpoints; rotate/revoke tested in cloud.
  - DoD: Unauth/revoked calls rejected on public URLs. _Traces:_ NFR-1/2, AC-7.
- [ ] **T-P7-07 (P2)** — Configure Gatekeeper rate limits/timeouts for cloud latency.
  - DoD: Stable runs against cloud; backpressure verified. _Traces:_ NFR-5, PLAN §19.
- [ ] **T-P7-08 (P2)** — If Ollama exposed at all, secure via ngrok policy / reverse proxy + auth.
  - DoD: No unauthenticated path to Ollama. _Traces:_ PRD Option 2 warnings.

### Phase P7 tests
- [ ] **T-P7-09 (P1)** — Integration: full game run against **cloud** MCP URLs (mock LLM ok).
- [ ] **T-P7-10 (P1)** — Security: unauth + revoked-token rejected on both cloud endpoints.

### Phase P7 Definition of Done (exit criteria)
- [ ] Public `cop_mcp_url` and `thief_mcp_url` are live and authenticated.
- [ ] Hybrid architecture confirmed; local machine/Ollama not exposed.
- [ ] Token revocation verified in the cloud.
- [ ] Ruff clean; coverage ≥ 85%.

---

## Phase P8 — Gmail JSON Report

**Goal:** After 6 valid sub-games, the cop automatically sends a **JSON-only** email report to the
destination address using the Gmail API.

**Priority:** P1 · **Status:** `[ ]` · **Traces:** PRD §8.6 (FR-E1..5), §12 (report contract), PLAN §10.5.

### Report builder (`services/report/builder.py`)
- [ ] **T-P8-01 (P1)** — Build the report JSON per PRD §12 contract.
  - Sub: `group_name`, `students[]`, `github_repo`, `cop_mcp_url`, `thief_mcp_url`, `timezone`,
    `sub_games[]`, `totals.{cop,thief}`. _Traces:_ FR-E5.
- [ ] **T-P8-02 (P1)** — Populate `sub_games[]` from `ResultCollector` (winner, moves, barriers, scores).
  - DoD: 6 entries; matches PLAN §10.4. _Traces:_ FR-S2.
- [ ] **T-P8-03 (P1)** — Populate `totals` from accumulated scores.
  - DoD: Totals equal sum of sub-game scores. _Traces:_ FR-S3.
- [ ] **T-P8-04 (P1)** — Validate output is strictly valid JSON (schema check).
  - DoD: Parser round-trips; no extra fields. _Traces:_ FR-E4.

### Emailer (`services/report/emailer.py`)
- [ ] **T-P8-05 (P1)** — Implement Gmail API send (auth per D-04) via Gatekeeper.
  - DoD: Sends to `email.to`; creds from env. _Traces:_ FR-E2/E3, NFR-5.
- [ ] **T-P8-06 (P1)** — Ensure email **body is JSON only** (no greeting/text/comments).
  - DoD: Body byte-for-byte equals report JSON. _Traces:_ FR-E4, AC-8.
- [ ] **T-P8-07 (P1)** — Trigger send automatically at end of full game (cop agent).
  - DoD: No manual step; fires only after 6 valid sub-games. _Traces:_ FR-E1, FR-L4, AC-2.
- [ ] **T-P8-08 (P2)** — Retry/handle Gmail quota/auth failures via Gatekeeper.
  - DoD: Transient failures retried; clear error on hard failure. _Traces:_ Risk, NFR-5.

### Phase P8 tests
- [ ] **T-P8-09 (P1)** — Unit: report builder produces schema-valid JSON for sample results.
- [ ] **T-P8-10 (P1)** — Unit: email body contains JSON only (no extra characters).
- [ ] **T-P8-11 (P1)** — Integration: end-of-game auto-send with **mocked** Gmail client.

### Phase P8 Definition of Done (exit criteria)
- [ ] JSON-only report email auto-sent to the destination after 6 valid sub-games.
- [ ] Report matches PRD §12 contract and validates as JSON.
- [ ] Gmail credentials sourced from env; failures handled.
- [ ] Ruff clean; coverage ≥ 85%.

---

## Phase P9 — Hardening, Scientific README & Final Audit

**Goal:** Bring the system to submission readiness: ≥85% coverage, zero Ruff violations, a scientific
README (Dec-POMDP, orchestration challenges, evidence), and a passing final checklist.

**Priority:** P1 · **Status:** `[ ]` · **Traces:** PRD §13 (acceptance), §18 (README), system-prompt audit.

### Test hardening & coverage
- [ ] **T-P9-01 (P1)** — Raise global coverage to **≥ 85%**; fill gaps in engine/orchestrator/report.
  - DoD: `uv run pytest` coverage ≥ 85% enforced. _Traces:_ NFR-8, AC-11.
- [ ] **T-P9-02 (P1)** — Add edge/failure tests: invalid inputs, external-dependency failures.
  - DoD: LLM/MCP/Gmail failure paths covered with mocks. _Traces:_ Testing rules.
- [ ] **T-P9-03 (P1)** — Full end-to-end integration test (mocked externals) asserting 6 valid sub-games + report.
  - DoD: Single test exercises full pipeline. _Traces:_ AC-2/3/8.
- [ ] **T-P9-04 (P1)** — Resolve all Ruff violations to **0**.
  - DoD: `uv run ruff check .` clean. _Traces:_ AC-11.

### Scientific README (`README.md`)
- [ ] **T-P9-05 (P1)** — Write installation/usage/config/examples/troubleshooting/credits/license.
  - DoD: README covers system-prompt mandatory sections. _Traces:_ PRD §18, README quality.
- [ ] **T-P9-06 (P1)** — Document the **Dec-POMDP** formal model ⟨n,S,{Aᵢ},P,R,{Ωᵢ},O,γ⟩.
  - DoD: Matches PRD §6; explains partial observability. _Traces:_ README §1.
- [ ] **T-P9-07 (P1)** — Document **orchestration challenges** (NL comms, no fixed protocol, ambiguity,
        partial observation, coordination, misunderstanding).
  - DoD: All six challenges addressed. _Traces:_ README §2.
- [ ] **T-P9-08 (P1)** — Add **evidence**: GUI screenshots, CLI logs, MCP comms logs, result analysis,
        learning curves (if Q-learning).
  - DoD: Artifacts in `assets/`/`results/` and embedded. _Traces:_ README §3.
- [ ] **T-P9-09 (P2)** — Add **cost analysis** for LLM/cloud/API usage.
  - DoD: Cost table present. _Traces:_ Research/results rules.
- [ ] **T-P9-10 (P1)** — Fill final report identity fields (`group_name`, `students`, `github_repo`,
        `cop_mcp_url`, `thief_mcp_url`). _Traces:_ D-01, FR-E5.

### Repository & deployment readiness
- [ ] **T-P9-11 (P1)** — Publish **public GitHub repo**; confirm no secrets in history.
  - DoD: Repo public; secret scan clean. _Traces:_ AC-10, Security.
- [ ] **T-P9-12 (P2)** — Add LICENSE and credits.
- [ ] **T-P9-13 (P2)** — Verify `uv.lock` committed and reproducible (`uv sync` clean clone).

### Final audit (system-prompt checklist)
- [ ] **T-P9-14 (P1)** — Run final readiness audit and record verdict (READY / CONDITIONAL / NOT).
  - DoD: Each checklist item justified. _Traces:_ system-prompt final checklist.

### Phase P9 Definition of Done (exit criteria)
- [ ] All PRD §13 acceptance criteria (AC-1..AC-11) pass.
- [ ] Coverage ≥ 85%; Ruff 0; README scientific & complete.
- [ ] Public repo live; secrets clean; deployment reproducible.

---

## Bonus — Cross-Group Competition (Optional, P3)

**Traces:** PRD §16, assignment §21–22. Submit within one week of publication.

- [ ] **T-BN-01 (P3)** — Agree shared JSON schema + match protocol with the opposing group.
  - DoD: Both sides validate identical schema. _Traces:_ "reports must match".
- [ ] **T-BN-02 (P3)** — Play sub-games 1–3: our cop vs their thief.
- [ ] **T-BN-03 (P3)** — Play sub-games 4–6: their cop vs our thief.
- [ ] **T-BN-04 (P3)** — Produce a **matching** combined JSON report with both groups.
  - DoD: Reports identical; mismatch ⇒ 0 for both. _Traces:_ PRD §22.
- [ ] **T-BN-05 (P3)** — Record bonus outcome (win=10 / lose=7 / tie=5); average if multiple series.

---

## Risk-Mitigation Task Tracker

Maps PRD §14 risks to concrete mitigation tasks.

| Risk (PRD §14) | Mitigation task(s) | Status |
|----------------|--------------------|--------|
| NL ambiguity ⇒ illegal/no action | T-P3-05, T-P5-06 (heuristic fallback) | `[ ]` |
| LLM latency / rate limits | T-P0-16..19, T-P7-07 (Gatekeeper) | `[ ]` |
| Exposing local Ollama | T-P7-05, T-P7-08 (hybrid, no exposure) | `[ ]` |
| Leaked keys/tokens | T-P0-03/04/11/20 (env + redaction) | `[ ]` |
| Sub-game technical failure | T-P1-19, T-P3-10/16 (auto-rerun) | `[ ]` |
| Cloud auth misconfig | T-P7-06, T-P7-10 (auth + revoke tests) | `[ ]` |
| Gmail quota/auth issues | T-P8-08 (retry) | `[ ]` |
| Non-matching bonus JSON | T-BN-01/04 (shared schema) | `[ ]` |

---

## Acceptance-Criteria Traceability Matrix

| Acceptance (PRD §13) | Covering tasks |
|----------------------|----------------|
| AC-1 two MCP servers (local+cloud) | T-P2-09/11, T-P7-02/03 |
| AC-2 one-command autonomous run | T-P3-14, T-P8-07 |
| AC-3 exactly 6 valid sub-games | T-P1-18/19, T-P3-10/16 |
| AC-4 ≤25 moves, ≤5 barriers | T-P1-11/14 |
| AC-5 config-driven board size | T-P0-09, T-P1-02, T-P6-02 |
| AC-6 natural-language messages | T-P5-02/07 |
| AC-7 auth + revocation | T-P2-13/14, T-P7-06/10 |
| AC-8 JSON-only email | T-P8-04/06/07 |
| AC-9 GUI shows state | T-P6-02..05 |
| AC-10 public repo + scientific README | T-P9-05..11 |
| AC-11 ≥85% coverage, 0 Ruff | T-P9-01/04 |

---

## Definition of Done — Project-Level (final gate)

The project is **submission-ready** only when:
- [ ] All P0–P9 phase DoDs are satisfied.
- [ ] All acceptance criteria (AC-1..AC-11) are green in the traceability matrix.
- [ ] Two MCP servers (cop, thief) run locally **and** in the cloud with token auth + revocation.
- [ ] One command runs a full autonomous game: 6 valid sub-games, NL communication, JSON email sent.
- [ ] Config drives all tunables; secrets only in env; nothing sensitive in Git.
- [ ] Coverage ≥ 85%; Ruff 0; files ≤ ~150 LOC; SDK-only GUI/CLI; Gatekeeper for all egress.
- [ ] Scientific README with Dec-POMDP model, orchestration challenges, and evidence.
- [ ] Final audit verdict recorded (T-P9-14).

---

## Change Log

| Date | Version | Change |
|------|---------|--------|
| 2026-06-21 | 1.0 | Initial phased backlog derived from PRD.md & PLAN.md |
