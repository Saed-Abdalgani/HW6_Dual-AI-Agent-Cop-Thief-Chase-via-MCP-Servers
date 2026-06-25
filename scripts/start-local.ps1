# One-command local run: starts MCP servers + plays 6 sub-games.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

if (-not (Test-Path .env)) {
    Copy-Item .env-example .env
    Write-Host "Created .env — add LLM_API_KEY if using strategy: llm"
}

$env:MCP_MODE = "http"
$env:MCP_COP_URL = "http://localhost:8001"
$env:MCP_THIEF_URL = "http://localhost:8002"

Write-Host "Verifying MCP endpoints..."
uv run cop-thief-verify-cloud
if ($LASTEXITCODE -ne 0) {
    Write-Host "Verify failed — starting game anyway (auto-launch will spawn servers)..."
}

Write-Host "Running 6 sub-games..."
uv run cop-thief
