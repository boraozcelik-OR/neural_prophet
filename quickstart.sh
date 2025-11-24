#!/usr/bin/env bash
set -euo pipefail

# Quickstart helper for Prophet Labs (government-grade stack).
# It can optionally install dependencies, render .env via ops.bootstrap,
# and start the dev servers. All actions are logged to stdout; detailed
# logs are still emitted by the underlying tools into the logs/ directory.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
INSTALL_SCRIPT="$PROJECT_ROOT/ops/shell/install_dependencies.sh"
BOOTSTRAP_MODULE="ops.bootstrap"
RUN_DEV_SCRIPT="$PROJECT_ROOT/ops/shell/run_dev.sh"

SKIP_INSTALL=false
SKIP_BOOTSTRAP=false
START_DEV=false
API_PORT=8000
FRONTEND_PORT=3000
ENVIRONMENT="dev"

usage() {
  cat <<USAGE
Usage: ./quickstart.sh [options]

Options:
  --skip-install       Skip dependency installation (system + pip/npm).
  --skip-bootstrap     Skip .env rendering via ops.bootstrap.
  --dev                Start backend + frontend dev servers after setup.
  --api-port <port>    Override API port (default: 8000).
  --frontend-port <p>  Override frontend port (default: 3000).
  --environment <env>  Environment label for bootstrap (dev|stage|prod, default: dev).
  -h, --help           Show this help message.
USAGE
}

log() { printf '[quickstart] %s\n' "$*"; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-install) SKIP_INSTALL=true; shift ;;
    --skip-bootstrap) SKIP_BOOTSTRAP=true; shift ;;
    --dev) START_DEV=true; shift ;;
    --api-port) API_PORT="$2"; shift 2 ;;
    --frontend-port) FRONTEND_PORT="$2"; shift 2 ;;
    --environment) ENVIRONMENT="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

log "Project root: $PROJECT_ROOT"
command -v python >/dev/null 2>&1 || { echo "python not found in PATH" >&2; exit 1; }

if ! $SKIP_INSTALL; then
  if [[ -x "$INSTALL_SCRIPT" ]]; then
    log "Running dependency installer ..."
    bash "$INSTALL_SCRIPT"
  else
    log "Installer not found at $INSTALL_SCRIPT; skipping install step."
  fi
else
  log "Skipping dependency installation as requested."
fi

if ! $SKIP_BOOTSTRAP; then
  log "Rendering .env via ops.bootstrap (environment=$ENVIRONMENT, api_port=$API_PORT, frontend_port=$FRONTEND_PORT) ..."
  python -m "$BOOTSTRAP_MODULE" --yes --environment "$ENVIRONMENT" --api-port "$API_PORT" --frontend-port "$FRONTEND_PORT"
else
  log "Skipping bootstrap as requested."
fi

if $START_DEV; then
  if [[ -x "$RUN_DEV_SCRIPT" ]]; then
    log "Starting dev services (API port $API_PORT, frontend port $FRONTEND_PORT) ..."
    API_PORT="$API_PORT" FRONTEND_PORT="$FRONTEND_PORT" bash "$RUN_DEV_SCRIPT"
  else
    log "Dev runner not found at $RUN_DEV_SCRIPT."
  fi
else
  log "Dev servers not started. Run: API_PORT=$API_PORT FRONTEND_PORT=$FRONTEND_PORT bash $RUN_DEV_SCRIPT"
fi

log "Quickstart complete."
