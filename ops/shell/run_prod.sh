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

log() { echo "[prod] $1"; }

if [ -d "$PROJECT_ROOT/.venv" ]; then
  # shellcheck disable=SC1091
  source "$PROJECT_ROOT/.venv/bin/activate"
fi

log "Building frontend assets"
cd "$PROJECT_ROOT/frontend/prophet-labs-console"
npm run build

log "Starting backend API (uvicorn) on ${API_HOST}:${API_PORT}"
cd "$PROJECT_ROOT"
python -m uvicorn prophet_labs.ui.api:app --host "$API_HOST" --port "$API_PORT" --workers "${RECOMMENDED_API_WORKERS:-1}" &
API_PID=$!

log "Serving frontend build with preview server on port ${FRONTEND_PORT}"
cd "$PROJECT_ROOT/frontend/prophet-labs-console"
npm run preview -- --host 0.0.0.0 --port "$FRONTEND_PORT" &
FE_PID=$!

trap 'log "Stopping services"; kill $API_PID $FE_PID 2>/dev/null' EXIT
wait
