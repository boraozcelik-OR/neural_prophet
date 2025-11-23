#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

if [ -f "$ENV_FILE" ]; then
  # shellcheck disable=SC1091
  source "$ENV_FILE"
fi

API_HOST=${API_HOST:-0.0.0.0}
API_PORT=${API_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-3000}

log() { echo "[dev] $1"; }

if [ -d "$PROJECT_ROOT/.venv" ]; then
  # shellcheck disable=SC1091
  source "$PROJECT_ROOT/.venv/bin/activate"
fi

log "Starting backend API on ${API_HOST}:${API_PORT}"
python -m uvicorn prophet_labs.ui.api:app --host "$API_HOST" --port "$API_PORT" &
API_PID=$!

log "Starting frontend dev server on 0.0.0.0:${FRONTEND_PORT}"
cd "$PROJECT_ROOT/frontend/prophet-labs-console"
npm run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT" &
FE_PID=$!

trap 'log "Stopping services"; kill $API_PID $FE_PID 2>/dev/null' EXIT
wait
