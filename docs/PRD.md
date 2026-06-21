# PRD — Dual AI Agent Cop–Thief Chase via MCP Servers

| Field | Value |
|-------|-------|
| Document | Product Requirements Document (PRD) |
| Project | `marl-cop-thief` — Two autonomous AI agents (Cop & Thief) playing a chase game over MCP |
| Assignment | HW6 — Conversation between two AI agents |
| Version | 1.0 (draft) |
| Status | Draft — pending review |
| Owner | `<group_name>` (to be filled) |
| Related docs | `docs/PLAN.md`, `docs/TODO.md`, `docs/PRD_game_engine.md`, `docs/PRD_qlearning.md`, `docs/PRD_nl_protocol.md` |

---

## 1. Purpose & Vision

Build a **complete autonomous orchestration pipeline** in which two independent AI agents — a **Cop**
and a **Thief** — play a turn-based chase game on a configurable 2D grid. The agents **communicate in
natural language** through **two separate MCP servers** and reason about each other's position from
**partial observation**.

The primary objective is to **prove a full, end-to-end working pipeline** between two autonomous AI
agents that runs **from start to finish without manual intervention** and emails a machine-parseable
JSON report at the end. Winning the game is secondary; the grade focus is **orchestration,
communication, and engineering quality**.

### 1.1 Vision Statement
> A self-driving multi-agent system where two LLM-driven agents negotiate, taunt, and deceive each
> other in free text, translate that language into grid actions through MCP tools, play 6 valid
> sub-games, and autonomously report results — all reproducible from a single configuration file.

---

## 2. Background & Problem Statement

Multi-agent coordination usually relies on rigid, fixed protocols (e.g., sending exact coordinates).
This assignment deliberately forbids relying on direct numeric coordinate transfer and instead
requires **natural-language messaging**, forcing the agents to handle **ambiguity, misunderstanding,
and partial observability**. The engineering challenge is to wrap this uncertainty in a robust,
secure, cloud-deployed orchestration pipeline.

---

## 3. Target Users & Stakeholders

| Stakeholder | Interest |
|-------------|----------|
| Course graders / automated checker | Parse the final JSON email; verify 6 valid sub-games, scores, MCP URLs |
| Project group (students) | Build, run, deploy, and demonstrate the system |
| Competing groups (bonus) | Play cross-group cop-vs-thief series with matching JSON reports |
| Developers / maintainers | Extend strategy, board size, deployment targets |
| Security reviewer | Verify auth tokens, no exposed local services, no leaked secrets |

---

## 4. Goals & Non-Goals

### 4.1 Goals (G)
- **G1** — Two **separate MCP servers** (cop, thief), each exposing tools only (no LLM inside server).
- **G2** — A **game engine / orchestrator (MCP client)** that owns game logic, calls the LLM, and
  invokes MCP tools.
- **G3** — Agents **exchange free-text natural-language messages** and interpret them; no reliance on
  exact numeric coordinate exchange.
- **G4** — Run **6 valid sub-games** automatically; invalid (technical-failure) sub-games are rerun.
- **G5** — Fully **configurable** via `config.yaml`/`config.json` — no hard-coded values.
- **G6** — **Cloud-deployed** MCP servers with two public URLs (`cop_mcp_url`, `thief_mcp_url`).
- **G7** — **Token-based authentication** with revocation capability; no unsafe local exposure.
- **G8** — **Automatic JSON-only email report** to the destination address at game end.
- **G9** — **GUI** visualizing grid, agents, barriers, movement, and scores.
- **G10** — Public **GitHub repo** with a **scientific README** (Dec-POMDP model, challenges, evidence).

### 4.2 Non-Goals (NG)
- **NG1** — Guaranteeing the cop/thief wins; strategy optimality is not the grading focus.
- **NG2** — Mandatory reinforcement learning (Q-learning is **optional**).
- **NG3** — Production-grade multi-tenant scaling beyond the assignment's needs.
- **NG4** — Human-in-the-loop play; the system must run autonomously.

---

## 5. Success Metrics / KPIs

| KPI | Target |
|-----|--------|
| Valid sub-games completed per run | Exactly **6** |
| Manual interventions during a full run | **0** |
| Email report format | **Valid JSON only**, no prose, parseable by checker |
| Config-driven board size change works | Yes (e.g., 5×5 → 7×7 with no code change) |
| Auth: unauthenticated MCP calls rejected | 100% |
| Natural-language turns (not raw coords) | 100% of inter-agent messages |
| Test coverage (global) | **≥ 85%** |
| Ruff violations | **0** |
| Max moves enforced per sub-game | **25** |
| Cop barriers enforced per sub-game | **≤ 5** |

---

## 6. Formal Model — Dec-POMDP

The game is modeled as a **Decentralized Partially Observable Markov Decision Process (Dec-POMDP)**:

$$\langle\, n,\ S,\ \{A_i\},\ P,\ R,\ \{\Omega_i\},\ O,\ \gamma\, \rangle$$

| Symbol | Meaning | This project |
|--------|---------|--------------|
| `n` | Number of agents | **2** (Cop, Thief) |
| `S` | State space | All `(cop_pos, thief_pos, barriers, move_count)` tuples on the grid |
| `{A_i}` | Action set per agent | Cop: 8 moves + `place_barrier` + `stay`; Thief: 8 moves + `stay` |
| `P` | Transition function | Deterministic grid dynamics with barrier blocking |
| `R` | Reward function | Scoring table (win/loss) + optional shaping (distance) |
| `{Ω_i}` | Observation space per agent | Partial: own position + natural-language messages, no exact opponent coords |
| `O` | Observation function | Maps state → each agent's partial observation + received NL message |
| `γ` | Discount factor | From config (default `0.95`) |

**Partial observability:** each agent observes its own position and a **free-text message** from the
opponent, then must **estimate** the opponent's position. This is detailed in `docs/PRD_nl_protocol.md`
and `docs/PRD_qlearning.md`.

---

## 7. Functional Requirements — Game Rules

### 7.1 Board
- **FR-B1** — Grid is 2D with cell coordinates `(row, col)`; default **5×5**.
- **FR-B2** — Board size is read from config (`grid_size`); **never hard-coded**.
- **FR-B3** — Cop and thief start at positions chosen **randomly or by strategy** (config-selectable).
- **FR-B4** — Start positions must be distinct and not on a barrier.

### 7.2 Movement
- **FR-M1** — Movement is allowed in **all 8 directions** (orthogonal + diagonal).
- **FR-M2** — A player may also **stay** (no-op) where rules allow.
- **FR-M3** — Moves that leave the board are illegal and rejected by the engine.
- **FR-M4** — A move **into or across a blocked (barrier) square is illegal** for both players.
- **FR-M5** — Players **take turns**; by default the **thief moves first**, then the cop.

### 7.3 Capture & Victory
- **FR-V1 (Cop wins)** — The cop wins when it occupies the **exact same square** as the thief (capture).
- **FR-V2 (Thief wins)** — The thief wins if it **survives 25 moves** without being captured.
- **FR-V3** — `max_moves` (default 25) is configurable and strictly enforced.

### 7.4 Barriers
- **FR-BR1** — On its turn, the cop may **place a barrier on its current square instead of moving**.
- **FR-BR2** — When placing a barrier, the cop **does not move** that turn.
- **FR-BR3** — A blocked square **cannot be entered or crossed** by either player.
- **FR-BR4** — The cop may place **at most 5 barriers per sub-game** (`max_barriers`, configurable).
- **FR-BR5** — The thief **cannot** place barriers.

### 7.5 Scoring
- **FR-S1** — Per-sub-game scoring follows the table below (values from config).

| Result | Cop score | Thief score |
|--------|-----------|-------------|
| Cop wins (capture) | `scoring.cop_win` = **20** | `scoring.thief_loss` = **5** |
| Thief wins (escape) | `scoring.cop_loss` = **5** | `scoring.thief_win` = **10** |

- **FR-S2** — A **full game = 6 sub-games**; scores accumulate.
- **FR-S3** — Theoretical group max = **90** (`3×20` as cop + `3×10` as thief); min = **30**.

### 7.6 Sub-game / Full-game Lifecycle
- **FR-L1** — A **sub-game** is a single chase round (≤ 25 moves).
- **FR-L2** — A **full game** contains **6 valid sub-games**.
- **FR-L3** — If a sub-game fails due to a **technical problem**, it **does not count** and must be
  **rerun** until 6 valid sub-games are recorded.
- **FR-L4** — A **final JSON report is emailed only after 6 valid sub-games** complete.

---

## 8. Functional Requirements — System

### 8.1 MCP Servers (two separate)
- **FR-MCP1** — Build a **Cop MCP server** and a **Thief MCP server** as **independent** services.
- **FR-MCP2** — Servers **expose tools only**; the **LLM is NOT inside the MCP server**.
- **FR-MCP3** — Each server exposes tools such as: `send_message`, `receive_message`,
  `verify/update position`, `choose_action`, and `communicate with game engine`.
- **FR-MCP4** — Tools validate inputs and return structured results to the client.
- **FR-MCP5** — Servers run **locally** (distinct ports) in Stage 1 and in the **cloud** in Stage 2.

### 8.2 Orchestrator / Game Engine (MCP client)
- **FR-O1** — The orchestrator owns **all game logic**: grid, movement, capture, barriers, scoring,
  turn order, sub-game/full-game loop, result collection, and report dispatch.
- **FR-O2** — The orchestrator is the **MCP client**: it calls the LLM, decides which tool to call,
  invokes MCP server tools, and feeds results back into the loop.
- **FR-O3** — Workflow per turn: engine sends context → LLM decides action/tool → client calls MCP
  tool → result returned to engine/LLM → game advances.
- **FR-O4** — The orchestrator detects technical failures and **reruns** invalid sub-games.

### 8.3 Natural-Language Communication
- **FR-NL1** — Agents exchange **free-text** messages (e.g., taunts, hints, bluffs), **not** fixed
  data such as `"I am at (2,3)"`.
- **FR-NL2** — The receiving agent must **interpret** the message and **estimate** opponent intent.
- **FR-NL3** — The system must function despite **ambiguity and misunderstanding** (graceful handling).
- **FR-NL4** — All inter-agent communication flows through the MCP `send/receive` tools.

### 8.4 LLM Integration
- **FR-LLM1** — Support **Option 1 (Cloud LLM API: OpenAI/Anthropic/Gemini)** as the default path.
- **FR-LLM2** — Support **Option 3 (Hybrid)**: local Ollama (`localhost:11434`) with MCP servers in
  the cloud; client makes only **outbound HTTPS** calls.
- **FR-LLM3** — **Never expose local Ollama directly** to the internet (security requirement).
- **FR-LLM4** — LLM provider, model name, endpoint, and timeouts come from **config/env**.

### 8.5 Decision-Making Strategy
- **FR-D1** — Provide at least one working strategy: **heuristic (Manhattan distance)** baseline.
- **FR-D2** — Optionally support **Tabular Q-Learning** (Bellman update) — not mandatory.
- **FR-D3** — Strategy is **selectable via config** (`strategy: heuristic | qlearning | llm`).

### 8.6 Email Report
- **FR-E1** — After 6 valid sub-games, the **cop agent automatically sends a summary email**.
- **FR-E2** — Destination: `rmisegal+uoh26b@gmail.com` (configurable).
- **FR-E3** — Preferred method: **Gmail API**.
- **FR-E4** — The email body must contain **JSON only** — no greetings, explanations, or comments.
- **FR-E5** — JSON schema includes: `group_name`, `students`, `github_repo`, `cop_mcp_url`,
  `thief_mcp_url`, `timezone`, `sub_games[]`, `totals.{cop,thief}`.

### 8.7 GUI
- **FR-G1** — GUI displays the grid, cop location, thief location, and barriers.
- **FR-G2** — GUI shows **movement over time** and **current scores**.
- **FR-G3** — GUI is a presentation layer only; it calls the **SDK**, never internal services.

### 8.8 Configuration
- **FR-C1** — All tunables live in `config.yaml`/`config.json` (see §11 schema).
- **FR-C2** — Required keys: `grid_size`, `max_moves`, `num_games`, `max_barriers`, and `scoring.*`.
- **FR-C3** — Secrets (API keys, tokens, Gmail creds) come from **env vars / `.env`**, never Git.

---

## 9. Non-Functional Requirements

| ID | Category | Requirement |
|----|----------|-------------|
| NFR-1 | Security | MCP servers require **auth tokens**; unauthenticated requests are rejected. |
| NFR-2 | Security | Tokens can be **revoked/rotated**; no secrets committed to Git. |
| NFR-3 | Security | **No direct public exposure** of local Ollama or local services. |
| NFR-4 | Reliability | A full run completes **6 valid sub-games with 0 manual steps**; auto-rerun on failure. |
| NFR-5 | Performance | LLM/MCP calls go through a **Gatekeeper** with rate limits, retries, queues, backpressure. |
| NFR-6 | Maintainability | Source files **≤ 150 LOC** where practical; one responsibility per component. |
| NFR-7 | Architecture | All business logic exposed via **SDK**; GUI/CLI/REST call SDK only. |
| NFR-8 | Testability | **≥ 85%** coverage; Ruff **0** violations; external calls mocked in tests. |
| NFR-9 | Portability | Board size, ports, providers, and endpoints fully **config-driven**. |
| NFR-10 | Observability | Structured logs for turns, messages, tool calls, and failures (no secret leakage). |
| NFR-11 | Reproducibility | Optional RNG **seed** in config for deterministic replays. |
| NFR-12 | Cost | Track LLM/API/cloud cost; document in README/results when relevant. |

---

## 10. Constraints & Assumptions

### 10.1 Constraints
- **Python** project managed **exclusively with `uv`** (no `pip`/`venv`/`virtualenv`).
- Communication between agents **must be natural language**, not raw coordinate transfer.
- MCP servers **must be deployable to the cloud** (e.g., Prefect Cloud or similar) with public URLs.
- Email body **must be JSON only**.

### 10.2 Assumptions
- A reachable LLM provider (cloud API or local Ollama) is available with valid credentials.
- A Gmail API project / OAuth credentials (or app password fallback) is available for sending mail.
- The cloud platform allows authenticated public HTTPS endpoints for the MCP servers.
- Group name, students, and GitHub URL are provided before the final report is generated.

---

## 11. Configuration Schema (authoritative key list)

| Parameter | Meaning | Default |
|-----------|---------|---------|
| `grid_size` | Board size `[rows, cols]` | `[5, 5]` |
| `max_moves` | Max moves per sub-game | `25` |
| `num_games` | Number of sub-games | `6` |
| `max_barriers` | Max barriers for cop | `5` |
| `scoring.cop_win` | Cop score if cop wins | `20` |
| `scoring.thief_win` | Thief score if thief wins | `10` |
| `scoring.cop_loss` | Cop score if thief escapes | `5` |
| `scoring.thief_loss` | Thief score if captured | `5` |
| `start_mode` | `random` or `strategy` | `random` |
| `thief_moves_first` | Turn order | `true` |
| `discount_gamma` | Dec-POMDP / Q-learning γ | `0.95` |
| `strategy` | `heuristic` \| `qlearning` \| `llm` | `heuristic` |
| `llm.provider` | `openai` \| `anthropic` \| `gemini` \| `ollama` | `openai` |
| `llm.model` | Model name | provider-specific |
| `llm.timeout_s` | LLM request timeout | `30` |
| `mcp.cop_url` / `mcp.thief_url` | MCP endpoints | localhost in Stage 1 |
| `gatekeeper.rate_limit_*` | Rate limit settings | from config |
| `email.to` | Report destination | `rmisegal+uoh26b@gmail.com` |
| `timezone` | Report timezone | `Asia/Jerusalem` |
| `seed` | Optional RNG seed | `null` |

> Secrets (LLM keys, MCP auth tokens, Gmail credentials) are **NOT** in config files — they live in
> `.env` / environment variables. See `.env-example`.

---

## 12. Final Report — JSON Contract

The cop emails exactly this structure (values filled at runtime):

```json
{
  "group_name": "Team-Alpha",
  "students": [],
  "github_repo": "https://github.com/team-alpha/marl-cop-thief",
  "cop_mcp_url": "https://cop-mcp-alpha.prefect.run",
  "thief_mcp_url": "https://thief-mcp-alpha.prefect.run",
  "timezone": "Asia/Jerusalem",
  "sub_games": [],
  "totals": { "cop": 90, "thief": 40 }
}
```

- `sub_games[]` records per-round outcome (winner, moves used, barriers used, scores).
- `totals` accumulates cop and thief scores across the 6 valid sub-games.
- **No extra text** in the email body.

---

## 13. Acceptance Criteria

The project is accepted when **all** hold:

- **AC-1** — Two separate MCP servers (cop, thief) are running and reachable (local + cloud).
- **AC-2** — A single command runs a **full autonomous game** to completion with **0 manual steps**.
- **AC-3** — Exactly **6 valid sub-games** are played; technically failed rounds are auto-rerun.
- **AC-4** — Each sub-game enforces **≤ 25 moves** and **≤ 5 cop barriers**.
- **AC-5** — Changing `grid_size` in config changes the board with **no code edits**.
- **AC-6** — Inter-agent messages are **natural language**, verifiable in logs.
- **AC-7** — MCP servers **reject unauthenticated** calls; tokens revocable.
- **AC-8** — A **JSON-only** report email is delivered to the destination address.
- **AC-9** — GUI shows grid, agents, barriers, movement, and scores.
- **AC-10** — Public GitHub repo with scientific README (Dec-POMDP, challenges, evidence).
- **AC-11** — **≥ 85%** test coverage and **0** Ruff violations.

---

## 14. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| NL ambiguity causes illegal/no action | Stalled turn | Engine validates; fallback to heuristic action |
| LLM latency / rate limits | Slow or failed run | Gatekeeper: retries, queue, backpressure, timeouts |
| Exposing local Ollama | Security breach | Hybrid arch; outbound-only HTTPS; never expose 11434 |
| Leaked API keys/tokens | Security breach | `.env` + `.gitignore`; secrets never in logs |
| Sub-game technical failure | Invalid results | Auto-detect + rerun until 6 valid sub-games |
| Cloud deploy auth misconfig | Open endpoints | Token auth enforced + revocation tested |
| Gmail API quota/auth issues | Report not sent | Retry + clear error; documented fallback |
| Non-matching bonus JSON | Bonus = 0 | Shared schema validation between groups |

---

## 15. Phased Milestones (PRD-level)

The build follows the assignment's recommended order. Detailed engineering tasks and Definition of
Done are in `docs/PLAN.md` and `docs/TODO.md`.

| Phase | Milestone | Exit criteria |
|-------|-----------|---------------|
| **P0** | Project scaffold + config + Gatekeeper | `uv` project, structure, config loads, Ruff clean |
| **P1** | Core game rules (grid, move, capture, barriers, scoring) | Unit-tested engine, deterministic with seed |
| **P2** | Two MCP servers (cop, thief) exposing tools | Tools callable; input validation; local ports |
| **P3** | Orchestrator + local end-to-end run | 6 sub-games run locally via MCP, no manual steps |
| **P4** | Decision strategy (heuristic; optional Q-learning) | Strategy selectable via config; baseline plays |
| **P5** | Natural-language messaging layer | Free-text turns; interpretation; ambiguity handling |
| **P6** | GUI | Visualizes grid, agents, barriers, movement, scores |
| **P7** | Cloud deployment + auth tokens | Public `cop_mcp_url`/`thief_mcp_url`; auth enforced |
| **P8** | Gmail API + automatic JSON report | JSON-only email delivered after 6 valid sub-games |
| **P9** | Hardening, tests ≥85%, scientific README, audit | Acceptance criteria all green; final checklist |

---

## 16. Out of Scope & Bonus

- **Out of scope:** human-controlled play; mandatory RL; large-scale productionization.
- **Bonus (optional, +10):** cross-group series — 3 sub-games Group A cop vs B thief, then 3 with
  roles swapped. Both groups must submit **matching** JSON reports (mismatch ⇒ 0 for both). Final
  bonus = average of valid series. Must be submitted within one week of publication.

---

## 17. Open Questions

- Final `group_name`, `students[]`, and `github_repo` values?
- Chosen LLM path: cloud API (Option 1) vs hybrid Ollama (Option 3)?
- Cloud platform: Prefect Cloud vs alternative?
- Gmail API OAuth vs service-account vs app-password fallback?
- Config format choice: `config.yaml` vs `config.json`?
