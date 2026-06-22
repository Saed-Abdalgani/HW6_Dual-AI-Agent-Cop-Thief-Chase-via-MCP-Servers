# Cop–Thief MCP System

> **Dual AI Agent Cop–Thief Chase via MCP Servers** (`marl-cop-thief` · v0.1.0)

A multi-agent chase simulation where a **Cop** pursues a **Thief** on a configurable grid. Two
independent MCP servers expose tools; a local orchestrator drives turns, natural-language
communication, and a JSON report email after six valid sub-games.

**Repository:** https://github.com/Saed-Abdalgani/HW6_Dual-AI-Agent-Cop-Thief-Chase-via-MCP-Servers

---

## 1. Formal Model — Dec-POMDP

The game is a **Decentralized Partially Observable Markov Decision Process**:

$$\langle\, n,\ S,\ \{A_i\},\ P,\ R,\ \{\Omega_i\},\ O,\ \gamma\, \rangle$$

| Symbol | Meaning | This project |
|--------|---------|--------------|
| `n` | Number of agents | **2** (Cop, Thief) |
| `S` | State space | `(cop_pos, thief_pos, barriers, move_count)` on the grid |
| `{A_i}` | Action sets | Cop: 8 moves + `place_barrier` + `stay`; Thief: 8 moves + `stay` |
| `P` | Transition | Deterministic grid dynamics with barrier blocking |
| `R` | Reward | Per-sub-game scoring table (win/loss points from config) |
| `{Ω_i}` | Observations | Own position + opponent NL message — **no exact opponent coords** |
| `O` | Observation fn | Maps global state → partial view + received message |
| `γ` | Discount | `discount_gamma` in config (default `0.95`) |

**Partial observability:** each agent maintains an **opponent estimate** (`OpponentEstimator`)
fused from NL cues and move history. See [`docs/PRD_nl_protocol.md`](docs/PRD_nl_protocol.md).

---

## 2. Orchestration Challenges

| Challenge | How we address it |
|-----------|-------------------|
| **Natural-language communication** | Free-text via MCP `send_message` / `receive_message`; encoder forbids raw coordinates |
| **No fixed protocol** | Agents infer intent from NL; parser extracts coarse direction/region cues |
| **Ambiguity** | Garbled or empty messages leave belief unchanged; heuristic fallback on LLM failure |
| **Partial observation** | Strategies use `opp_estimate`, not ground-truth opponent position |
| **Coordination** | Turn controller enforces thief-first order; engine is rules authority |
| **Misunderstanding** | `LlmClient` falls back to Manhattan heuristic; `ActionValidator` blocks illegal moves |

---

## 3. Evidence

| Artifact | Location | How to reproduce |
|----------|----------|------------------|
| CLI full-game log | terminal | `uv run cop-thief` |
| NL transcripts (6 sub-games) | `results/nl_transcript_subgame_*.jsonl` | Auto-written each run |
| GUI board capture | `assets/gui_phase6_board.ps` | Press **Capture** in GUI |
| GUI preview screenshot | `assets/gui_phase6_preview.png` | Save from GUI (gitignored) |
| Integration test trace | `tests/integration/test_full_pipeline.py` | `uv run pytest tests/integration/test_full_pipeline.py -v` |
| Coverage report | `htmlcov/` | `uv run pytest tests/` |

Example transcript line (coordinate-free):

```json
{"turn": 1, "from": "thief", "text": "Slipping toward the upper edge."}
```

---

## 4. Installation

**Requirements:** Python ≥ 3.11, [uv](https://docs.astral.sh/uv/)

```bash
git clone https://github.com/Saed-Abdalgani/HW6_Dual-AI-Agent-Cop-Thief-Chase-via-MCP-Servers.git
cd HW6_Dual-AI-Agent-Cop-Thief-Chase-via-MCP-Servers
uv sync --all-extras
cp .env-example .env   # fill secrets (never commit .env)
```

---

## 5. Usage

### Autonomous full game (CLI)

```bash
uv run cop-thief
```

Runs six valid sub-games with zero manual steps; dispatches JSON report when `GMAIL_ACCESS_TOKEN` is set.

### MCP servers (local)

```bash
uv run python -m cop_thief.mcp_servers.cop_server    # default :8001
uv run python -m cop_thief.mcp_servers.thief_server  # default :8002
```

### GUI replay

```bash
uv run cop-thief-gui
```

### Cloud verification

```bash
set CONFIG_PATH=config/config.cloud.yaml
uv run cop-thief-verify-cloud
```

See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for Docker and Render-style deployment.

---

## 6. Configuration

All tunables live in `config/config.yaml`. Secrets **only** in environment variables (see `.env-example`).

| Key | Purpose | Default |
|-----|---------|---------|
| `grid_size` | Board rows × cols | `[5, 5]` |
| `max_moves` | Sub-game move cap | `25` |
| `num_games` | Valid sub-games per full game | `6` |
| `max_barriers` | Cop barrier budget | `5` |
| `strategy` | `heuristic` \| `qlearning` \| `llm` | `heuristic` |
| `mcp.cop_url` / `mcp.thief_url` | MCP base URLs | localhost ports |
| `report.*` | JSON report identity fields | see config |
| `email.to` | Report destination | configured address |

**Report identity** (update before submission):

```yaml
report:
  group_name: "Your-Team-Name"
  students: ["Name One", "Name Two"]
  github_repo: "https://github.com/Saed-Abdalgani/HW6_Dual-AI-Agent-Cop-Thief-Chase-via-MCP-Servers"
```

---

## 7. Cost Analysis

Estimated per full game (6 sub-games, ~150 turns, heuristic strategy with optional LLM):

| Resource | Assumption | Est. cost |
|----------|------------|-----------|
| OpenAI `gpt-4o-mini` | ~300 tokens/turn × 150 turns | ~$0.05–0.15 |
| Cloud MCP (Render free tier) | 2 web services | $0 (free tier) |
| Gmail API | 1 send/request | $0 |
| Local compute | CLI + tests | $0 |

With `strategy: heuristic`, LLM calls are used only for NL messaging fallback paths; set
`strategy: llm` for full LLM decisions (higher cost). Gatekeeper rate limits prevent runaway spend.

---

## 8. Testing & Quality

```bash
uv run ruff check .
uv run pytest tests/
```

- Global coverage gate: **≥ 85%**
- Ruff violations: **0**
- Source files: **≤ ~150 LOC** each

Final audit: [`docs/FINAL_AUDIT.md`](docs/FINAL_AUDIT.md)

---

## 9. Troubleshooting

| Symptom | Fix |
|---------|-----|
| `LLM_API_KEY not set` | Export key or use `strategy: heuristic` with injected test caller |
| MCP connection refused | Start both servers or use default in-process direct MCP (CLI) |
| `GMAIL_ACCESS_TOKEN not set` | Email skipped; set OAuth token to send report |
| Coverage below 85% | Run full suite: `uv run pytest tests/` |
| Cloud auth failures | Rotate `MCP_*_TOKEN`; run `cop-thief-verify-cloud` |

---

## 10. Architecture (summary)

```
CLI / GUI  →  CopThiefSDK  →  GameLoop / TurnController
                ↓                    ↓
           Gatekeeper  →  LLM · MCP · Gmail
                ↓
         Engine (rules) + Strategy + NL encoder/parser
```

Details: [`docs/PLAN.md`](docs/PLAN.md) · Requirements: [`docs/PRD.md`](docs/PRD.md)

---

## 11. Contribution

1. Follow `uv` tooling only (no `pip` / `venv`).
2. Keep modules ≤ ~150 LOC; add tests for new logic.
3. Route external calls through `Gatekeeper`.
4. Update relevant docs and `docs/TODO.md`.

---

## 12. Credits & License

Course project — Multi-Agent Reinforcement Learning (UOH). Built with Python, FastMCP, httpx, Tkinter.

**License:** [MIT](LICENSE)
