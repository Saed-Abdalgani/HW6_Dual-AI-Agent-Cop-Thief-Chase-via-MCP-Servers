# How To Use The Project And Challenge Other Groups

## Local Setup

Install dependencies and verify the project:

```powershell
uv sync --all-extras
uv run ruff check .
uv run pytest tests/
```

Fill your team identity in `config/config.yaml` before producing the final report:

```yaml
report:
  group_name: "Your-Team-Name"
  students: ["Student One", "Student Two"]
```

## API Key Setup

This project supports a public cloud LLM through a normal API key. Put the key in an environment variable named `LLM_API_KEY`.

For PowerShell:

```powershell
$env:LLM_API_KEY="<your-provider-api-key>"
```

For a persistent local setup, copy `.env-example` to `.env` and fill:

```text
LLM_API_KEY=<your-provider-api-key>
```

Choose the provider/model in `config/config.yaml`:

```yaml
llm:
  provider: openai
  model: gpt-4o-mini
  timeout_s: 30
  base_url: null
```

To make the agents use the LLM for decisions, set:

```yaml
strategy: llm
```

If `strategy: heuristic` is left enabled, the project can still run mostly without model calls, but setting `LLM_API_KEY` is recommended for the full assignment flow and cloud verification.

Run a complete autonomous local game:

```powershell
$env:LLM_API_KEY="<your-provider-api-key>"
uv run cop-thief
```

Run the two local MCP servers manually when you want to inspect server behavior:

```powershell
uv run python -m cop_thief.mcp_servers.cop_server
uv run python -m cop_thief.mcp_servers.thief_server
```

Open the GUI:

```powershell
uv run cop-thief-gui
```

## Cloud Deployment

Deploy the three services defined in `deploy/render.yaml`:

- `cop-thief-state`
- `cop-thief-cop-mcp`
- `cop-thief-thief-mcp`

Set these environment variables in the cloud provider:

```text
LLM_API_KEY=<your-provider-api-key>
MCP_COP_TOKEN=<strong temporary token>
MCP_THIEF_TOKEN=<strong temporary token>
MCP_STATE_TOKEN=<shared state token>
MCP_STATE_URL=https://your-state-service-url
MCP_COP_URL=https://your-cop-mcp-url
MCP_THIEF_URL=https://your-thief-mcp-url
```

Verify the deployed cloud endpoints from your local machine:

```powershell
$env:CONFIG_PATH="config/config.cloud.yaml"
$env:MCP_COP_TOKEN="<cop-token>"
$env:MCP_THIEF_TOKEN="<thief-token>"
uv run cop-thief-verify-cloud
```

## Internal Submission Run

For the normal internal assignment submission, set the Gmail OAuth token and run the full game:

```powershell
$env:LLM_API_KEY="<your-provider-api-key>"
$env:GMAIL_ACCESS_TOKEN="<google-oauth-token>"
uv run cop-thief
```

The LLM uses `LLM_API_KEY`. The email sender uses the Gmail variables from `.env-example`; use `GMAIL_ACCESS_TOKEN` for OAuth or `GMAIL_USER` plus `GMAIL_APP_PASSWORD` for the simpler development path. The email body must contain only the structured JSON report. The project report builder already serializes the internal report as strict JSON.

## Challenge Another Group

Exchange these details with the other group:

- GitHub repository URL
- Cop MCP URL
- Thief MCP URL
- Temporary match tokens only

Do not share permanent secrets or personal API keys.

Play 6 valid sub-games:

- Games 1-3: your cop agent plays against their thief agent.
- Games 4-6: their cop agent plays against your thief agent.

Both groups must submit matching bonus reports. The JSON data must agree exactly, otherwise the bonus series can be cancelled.

The bonus report should include:

- `report_type: "bonus_game"`
- both group names
- both GitHub repository links
- all four MCP URLs
- timezone
- students for both groups
- all 6 sub-games
- totals by group
- bonus claim for each group
- `mutual_agreement: true`

## Practical Match Checklist

Before challenging another group:

- Run `uv run pytest tests/` locally.
- Set `LLM_API_KEY` locally and in the cloud provider.
- Deploy both MCP servers and the shared state service.
- Confirm both MCP URLs are public HTTPS URLs.
- Run `uv run cop-thief-verify-cloud`.
- Use temporary match tokens and rotate them after the match.
- Save the 6-game transcript and final JSON report for evidence.

Note: the repository currently automates the internal JSON email report. For bonus competition, prepare the extended `bonus_game` JSON carefully so both groups submit exactly the same result.
