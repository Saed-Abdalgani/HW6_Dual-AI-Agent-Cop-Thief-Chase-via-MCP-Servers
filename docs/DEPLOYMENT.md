# Phase P7 Deployment Guide

## Architecture

Deploy **three** Docker services from the same image:

| Service | Command | Role |
|---------|---------|------|
| `cop-thief-state` | `uv run cop-thief-state` | Shared JSON game state (required for two MCP containers) |
| `cop-thief-cop-mcp` | `SERVER_ROLE=cop` | Cop MCP tools over SSE |
| `cop-thief-thief-mcp` | `SERVER_ROLE=thief` | Thief MCP tools over SSE |

The orchestrator stays local (or CI) and calls public HTTPS MCP URLs outbound only.
Ollama or local LLM ports are never exposed.

## Required Secrets

Set these as Render environment variables. Never commit real values.

| Variable | Services | Purpose |
|----------|----------|---------|
| `MCP_STATE_TOKEN` | state, cop, thief | Auth for shared state storage |
| `MCP_COP_TOKEN` | cop, thief, local verifier | Bearer token for cop MCP calls |
| `MCP_THIEF_TOKEN` | cop, thief, local verifier | Bearer token for thief MCP calls |
| `MCP_STATE_URL` | cop, thief | Public HTTPS state-service base URL |
| `MCP_COP_URL` | cop, thief, local verifier | Public HTTPS cop MCP base URL |
| `MCP_THIEF_URL` | cop, thief, local verifier | Public HTTPS thief MCP base URL |
| `MCP_REVOKED_TOKENS` | cop, thief | Optional comma-separated revoked tokens |
| `SERVER_ROLE` | cop, thief | `cop` or `thief`; set by blueprint |
| `LLM_API_KEY` | local orchestrator | Required only when using LLM strategy/provider |
| `GMAIL_ACCESS_TOKEN` | local orchestrator | Required only for final email dispatch |

Minimum shared secrets on **all three** cloud services:

- `MCP_STATE_TOKEN` — bearer token for the shared state service
- `MCP_COP_TOKEN` — orchestrator → cop MCP
- `MCP_THIEF_TOKEN` — orchestrator → thief MCP

On both MCP services also set:

- `MCP_STATE_URL` — HTTPS base URL of the state service (e.g. `https://cop-thief-state.onrender.com`)
- `MCP_COP_URL` / `MCP_THIEF_URL` — public HTTPS base URLs of each MCP service

Optional revocation:

- `MCP_REVOKED_TOKENS` — comma-separated tokens rejected after rotation

## Local cloud simulation

```bash
cp .env-example .env   # fill MCP_* and MCP_STATE_TOKEN
docker compose -f docker-compose.cloud.yml up --build
```

Then point a local config at `http://localhost:8001` and `http://localhost:8002`.

## Render deployment

1. Create a Render blueprint from `deploy/render.yaml`.
2. Set sync=false secrets in the Render dashboard for every `MCP_*` key.
3. After the state service is live, set `MCP_STATE_URL` on both MCP services.
4. After MCP services are live, set `MCP_COP_URL` and `MCP_THIEF_URL` (HTTPS, no trailing path).

## Configure the local orchestrator

```bash
set MCP_COP_URL=https://<cop-service-url>
set MCP_THIEF_URL=https://<thief-service-url>
set MCP_MODE=http
set CONFIG_PATH=config/config.cloud.yaml
uv run cop-thief-verify-cloud
```

To verify revocation, set `MCP_TEST_REVOKED_TOKEN` locally and include the same token in
`MCP_REVOKED_TOKENS` on both MCP services.

Run a full game against cloud MCP (mocked or real LLM):

```bash
uv run cop-thief
```

The SDK auto-selects remote MCP when HTTPS cloud URLs are configured.
`config/config.cloud.yaml` pins `mcp.mode: http`; keep that value for deployed
MCP verification and full submission runs.

## Acceptance Checks

- Valid token reaches both public MCP endpoints.
- Bad token is rejected on both endpoints.
- Revoked token is rejected on both endpoints after redeploy.
- Full game completes over remote MCP URLs (integration test simulates this locally).
- Local client makes outbound HTTPS calls only; no local Ollama port is published.

## Optional live test

```bash
set MCP_COP_URL=https://...
set MCP_THIEF_URL=https://...
uv run pytest -m live_cloud
```
