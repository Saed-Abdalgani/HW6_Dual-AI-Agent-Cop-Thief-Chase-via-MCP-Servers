# Phase P7 Deployment Guide

## Architecture

Deploy two independent Docker services from the same image:

- Cop MCP: `SERVER_ROLE=cop`
- Thief MCP: `SERVER_ROLE=thief`

The orchestrator remains local or CI-hosted and calls the public HTTPS MCP URLs outbound only.
Ollama or local LLM ports are never exposed.

## Required Secrets

Set these on both cloud services:

- `MCP_COP_TOKEN`
- `MCP_THIEF_TOKEN`

Optional revocation:

- `MCP_REVOKED_TOKENS`: comma-separated old tokens to reject after rotation.

## Deploy

Build and run one role locally:

```bash
docker build -t cop-thief-mcp .
docker run --rm -p 8001:8001 --env-file .env -e SERVER_ROLE=cop cop-thief-mcp
```

For Render-style deployments, use `deploy/render.yaml`. For another Docker-capable cloud, create two
web services from `Dockerfile` and set the `SERVER_ROLE` value per service.

## Configure Public URLs

After deployment, update `config/config.cloud.yaml`:

```yaml
mcp:
  cop_url: "https://<cop-service-url>"
  thief_url: "https://<thief-service-url>"
```

Then run:

```bash
set CONFIG_PATH=config/config.cloud.yaml
uv run cop-thief-verify-cloud
```

To verify revocation, set `MCP_TEST_REVOKED_TOKEN` locally and include the same token in
`MCP_REVOKED_TOKENS` on both cloud services.

## Acceptance Checks

- Valid token reaches both public MCP endpoints.
- Bad token is rejected on both endpoints.
- Revoked token is rejected after redeploy.
- Local client makes outbound HTTPS calls only; no local Ollama or workstation port is exposed.
