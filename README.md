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

## GUI Replay (Phase P6)

Launch the SDK-only Tkinter replay GUI:

```bash
uv run cop-thief-gui
```

The GUI runs autonomous sub-games, animates SDK replay frames, shows scores and the latest NL
message, and can capture board evidence into `assets/`.

![Cop-Thief GUI preview](assets/gui_phase6_preview.png)

## Cloud MCP Deployment (Phase P7)

Build one Docker image and run it twice, once with `SERVER_ROLE=cop` and once with
`SERVER_ROLE=thief`. After replacing the URLs in `config/config.cloud.yaml`, verify public auth:

```bash
set CONFIG_PATH=config/config.cloud.yaml
uv run cop-thief-verify-cloud
```

See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for Docker, Render-style service config, token
rotation, and revocation checks.

## JSON Email Report (Phase P8)

After a full six-sub-game run, the SDK builds the PRD section 12 JSON report and dispatches it
through Gmail API when `GMAIL_ACCESS_TOKEN` is present:

```bash
set GMAIL_ACCESS_TOKEN=<oauth-access-token>
uv run cop-thief
```

The email body is the report JSON only. Identity fields live in `config/config.yaml` under `report`.


## Documentation

See [`docs/`](docs/) for:
- [`PRD.md`](docs/PRD.md) — Product Requirements Document
- [`PLAN.md`](docs/PLAN.md) — Architecture & Engineering Plan
- [`TODO.md`](docs/TODO.md) — Phased task backlog

---

*Full scientific README (Dec-POMDP model, orchestration challenges, evidence) will be written in Phase P9.*
