# Cop–Thief MCP System

> **Dual AI Agent Cop–Thief Chase via MCP Servers**
> (`marl-cop-thief` · v0.1.0)

A multi-agent reinforcement-learning simulation where a **Cop** agent chases a **Thief** agent on a grid, using independent MCP (Model Context Protocol) servers for communication and an LLM-driven orchestrator for decision-making.

## Quick Start

```bash
# Install dependencies
uv sync --all-extras

# Run the full autonomous game (6 valid sub-games)
uv run cop-thief
```

## Running MCP Servers Locally (Phase P2)

You can run the independent Cop and Thief MCP servers on their distinct local ports (defined in the configuration file, default ports 8001 and 8002):

```bash
# Start the Cop MCP server
uv run python -m cop_thief.mcp_servers.cop_server

# Start the Thief MCP server
uv run python -m cop_thief.mcp_servers.thief_server
```

## Natural-Language Transcripts (Phase P5)

Every orchestrated turn sends a coordinate-free free-text message through MCP. Sub-game transcripts
are written as JSON Lines files under `results/nl_transcript_subgame_<n>.jsonl`.


## Documentation

See [`docs/`](docs/) for:
- [`PRD.md`](docs/PRD.md) — Product Requirements Document
- [`PLAN.md`](docs/PLAN.md) — Architecture & Engineering Plan
- [`TODO.md`](docs/TODO.md) — Phased task backlog

---

*Full scientific README (Dec-POMDP model, orchestration challenges, evidence) will be written in Phase P9.*
