#!/usr/bin/env bash
set -euo pipefail

# Prophet Labs quickstart (government-grade). A compact launcher that can:
# 1) Optionally install dependencies (system + python + frontend) via ops scripts
# 2) Render .env with the bootstrapper
# 3) Start dev services (API + frontend)
# 4) Provide a lightweight Python wizard for interactive setup

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
INSTALL_SCRIPT="$PROJECT_ROOT/ops/shell/install_dependencies.sh"
BOOTSTRAP_MODULE="ops.bootstrap"
RUN_DEV_SCRIPT="$PROJECT_ROOT/ops/shell/run_dev.sh"
DEFAULT_API_PORT=8000
DEFAULT_FRONTEND_PORT=3000
DEFAULT_ENVIRONMENT="dev"

SKIP_INSTALL=false
SKIP_BOOTSTRAP=false
START_DEV=false
WIZARD=false
API_PORT="$DEFAULT_API_PORT"
FRONTEND_PORT="$DEFAULT_FRONTEND_PORT"
ENVIRONMENT="$DEFAULT_ENVIRONMENT"

usage() {
  cat <<USAGE
Usage: ./quickstart.sh [options]

Options:
  --skip-install         Skip dependency installation.
  --skip-bootstrap       Skip .env rendering via ops.bootstrap.
  --dev                  Start backend + frontend dev servers after setup.
  --wizard               Launch interactive Python wizard to set options.
  --api-port <port>      API port (default: $DEFAULT_API_PORT).
  --frontend-port <p>    Frontend port (default: $DEFAULT_FRONTEND_PORT).
  --environment <env>    Environment label (dev|stage|prod). Default: $DEFAULT_ENVIRONMENT
  -h, --help             Show this help message.
USAGE
}

log() { printf '[quickstart] %s\n' "$*"; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-install) SKIP_INSTALL=true; shift ;;
    --skip-bootstrap) SKIP_BOOTSTRAP=true; shift ;;
    --dev) START_DEV=true; shift ;;
    --wizard) WIZARD=true; shift ;;
    --api-port) API_PORT="$2"; shift 2 ;;
    --frontend-port) FRONTEND_PORT="$2"; shift 2 ;;
    --environment) ENVIRONMENT="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

command -v python >/dev/null 2>&1 || { echo "python not found in PATH" >&2; exit 1; }
mkdir -p "$PROJECT_ROOT/logs"

if $WIZARD; then
  # Simple text UI to confirm steps and override ports/env without editing flags
  readarray -t wizard_opts < <(python - <<'PY'
from __future__ import annotations
import json

def ask(prompt: str, default: bool) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        resp = input(f"{prompt} {suffix}: ").strip().lower()
        if not resp:
            return default
        if resp in {"y", "yes"}:
            return True
        if resp in {"n", "no"}:
            return False

install = ask("Run dependency installation?", True)
bootstrap = ask("Render .env via bootstrap?", True)
dev = ask("Start dev services?", False)
api = input("API port [8000]: ").strip() or "8000"
frontend = input("Frontend port [3000]: ").strip() or "3000"
env = input("Environment [dev]: ").strip() or "dev"
print(json.dumps([install, bootstrap, dev, api, frontend, env]))
PY
  )
  SKIP_INSTALL=$([[ "${wizard_opts[0]}" == "true" ]] && echo false || echo true)
  SKIP_BOOTSTRAP=$([[ "${wizard_opts[1]}" == "true" ]] && echo false || echo true)
  START_DEV=$([[ "${wizard_opts[2]}" == "true" ]] && echo true || echo false)
  API_PORT="${wizard_opts[3]}"
  FRONTEND_PORT="${wizard_opts[4]}"
  ENVIRONMENT="${wizard_opts[5]}"
fi

log "Project root: $PROJECT_ROOT"
log "Options => install:$([[ $SKIP_INSTALL == false ]] && echo yes || echo no) bootstrap:$([[ $SKIP_BOOTSTRAP == false ]] && echo yes || echo no) dev:$([[ $START_DEV == true ]] && echo yes || echo no) env:$ENVIRONMENT api:$API_PORT frontend:$FRONTEND_PORT"

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
  log "Rendering .env via ops.bootstrap ..."
  python -m "$BOOTSTRAP_MODULE" --yes --environment "$ENVIRONMENT" --api-port "$API_PORT" --frontend-port "$FRONTEND_PORT"
else
  log "Skipping bootstrap as requested."
fi

if $START_DEV; then
  if [[ -x "$RUN_DEV_SCRIPT" ]]; then
    log "Starting dev services (API=$API_PORT, UI=$FRONTEND_PORT) ..."
    API_PORT="$API_PORT" FRONTEND_PORT="$FRONTEND_PORT" bash "$RUN_DEV_SCRIPT"
  else
    log "Dev runner not found at $RUN_DEV_SCRIPT."
  fi
else
  log "Dev servers not started. Run manually with: API_PORT=$API_PORT FRONTEND_PORT=$FRONTEND_PORT bash $RUN_DEV_SCRIPT"
fi

log "Quickstart complete."
