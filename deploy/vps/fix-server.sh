#!/bin/bash
# Paste this entire file into GCP SSH (browser terminal). Fixes bind + restart + local test.
set -euo pipefail

PUBLIC_IP="${PUBLIC_IP:-136.112.135.83}"
REPO_DIR="$HOME/HW6_Dual-AI-Agent-Cop-Thief-Chase-via-MCP-Servers"

if [ ! -d "$REPO_DIR" ]; then
  git clone https://github.com/Saed-Abdalgani/HW6_Dual-AI-Agent-Cop-Thief-Chase-via-MCP-Servers.git "$REPO_DIR"
fi
cd "$REPO_DIR"

# Keep existing tokens if .env already exists; otherwise generate new ones.
if [ ! -f .env ]; then
  cat > .env <<EOF
MCP_STATE_TOKEN=$(openssl rand -hex 24)
MCP_COP_TOKEN=$(openssl rand -hex 24)
MCP_THIEF_TOKEN=$(openssl rand -hex 24)
MCP_REVOKED_TOKENS=
EOF
fi

# Public URLs for client config + force bind on all interfaces inside containers.
cat > .env.deploy <<EOF
$(grep -E '^MCP_(STATE|COP|THIEF)_TOKEN=' .env || true)
MCP_REVOKED_TOKENS=
MCP_COP_URL=http://${PUBLIC_IP}:8001
MCP_THIEF_URL=http://${PUBLIC_IP}:8002
EOF

cat > docker-compose.override.yml <<EOF
services:
  state:
    environment:
      MCP_STATE_HOST: "0.0.0.0"
  cop-mcp:
    environment:
      MCP_HOST: "0.0.0.0"
      MCP_COP_URL: http://${PUBLIC_IP}:8001
      MCP_THIEF_URL: http://${PUBLIC_IP}:8002
  thief-mcp:
    environment:
      MCP_HOST: "0.0.0.0"
      MCP_COP_URL: http://${PUBLIC_IP}:8001
      MCP_THIEF_URL: http://${PUBLIC_IP}:8002
EOF

if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker "$USER" || true
fi

set -a
# shellcheck disable=SC1091
source .env
# shellcheck disable=SC1091
source .env.deploy
set +a

sudo docker compose -f docker-compose.cloud.yml down || true
sudo docker compose -f docker-compose.cloud.yml up -d --build

echo ""
echo "Waiting for ports..."
sleep 8
sudo docker compose -f docker-compose.cloud.yml ps
echo ""
ss -lntp | grep -E ':8001|:8002|:8090' || true
echo ""
curl -s -o /dev/null -w "localhost:8001 => %{http_code}\n" http://127.0.0.1:8001/ || echo "8001 FAILED"
curl -s -o /dev/null -w "localhost:8002 => %{http_code}\n" http://127.0.0.1:8002/ || echo "8002 FAILED"

echo ""
echo "========== TOKENS (put in PC .env) =========="
grep -E '^MCP_(STATE|COP|THIEF)_TOKEN=' .env
echo "MCP_COP_URL=http://${PUBLIC_IP}:8001"
echo "MCP_THIEF_URL=http://${PUBLIC_IP}:8002"
echo "============================================="
echo ""
echo "If localhost tests FAILED, run:"
echo "  sudo docker compose -f docker-compose.cloud.yml logs --tail=50"
