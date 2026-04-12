#!/usr/bin/env bash
# ============================================================
# WorkReady Simulation — runtime start script
#
# Starts Caddy (reverse proxy + static file server) and the
# WorkReady API (uvicorn). Used identically by:
#   - Docker CMD
#   - Bare-metal systemd service
#   - Manual invocation
#
# Reads domains from domains.env and API config from .env.
# ============================================================

set -euo pipefail

WORKREADY_DIR="${WORKREADY_DIR:-/opt/workready}"

# Load environment files if they exist
[ -f "$WORKREADY_DIR/domains.env" ] && set -a && source "$WORKREADY_DIR/domains.env" && set +a
[ -f "$WORKREADY_DIR/.env" ] && set -a && source "$WORKREADY_DIR/.env" && set +a

# Ensure uv is on PATH
export PATH="$HOME/.local/bin:$PATH"

# Set DB path if not already set
export WORKREADY_DB="${WORKREADY_DB:-$WORKREADY_DIR/data/workready.db}"

# Point the API at the job data
export SITES_DIR="$WORKREADY_DIR"

echo "[workready] Starting WorkReady simulation..."
echo "[workready] DB: $WORKREADY_DB"
echo "[workready] Caddyfile: $WORKREADY_DIR/Caddyfile"

# Generate the Caddyfile from template if domains are set
# Caddy natively supports {$ENV_VAR} in Caddyfiles, so we just
# need the env vars to be set before Caddy starts.

# Start Caddy in the background
echo "[workready] Starting Caddy..."
caddy run --config "$WORKREADY_DIR/Caddyfile" --adapter caddyfile &
CADDY_PID=$!

# Give Caddy a moment to bind
sleep 1

# Start the API in the foreground
echo "[workready] Starting WorkReady API on :8000..."
cd "$WORKREADY_DIR/workready-api"

# Use uv run to ensure the venv is active
exec uv run --quiet uvicorn workready_api.app:app \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info
