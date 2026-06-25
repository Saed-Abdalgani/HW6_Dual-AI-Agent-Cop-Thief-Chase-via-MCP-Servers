# Run cloud MCP verification from Windows (loads .env automatically via uv).
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

$env:CONFIG_PATH = "config/config.cloud.yaml"
$env:MCP_MODE = "http"

uv run cop-thief-verify-cloud
