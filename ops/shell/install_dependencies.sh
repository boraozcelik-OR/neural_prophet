#!/usr/bin/env bash
set -euo pipefail

# Entry point for installing system and language dependencies for Prophet Labs.
# Dispatches to OS-specific installers when available.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

log() { echo "[install] $1"; }

detect_os() {
  uname_out="$(uname -s)"
  case "${uname_out}" in
    Linux*)   os=Linux;;
    Darwin*)  os=Darwin;;
    CYGWIN*|MINGW*|MSYS*) os=Windows;;
    *)        os=Unknown;;
  esac
  echo "$os"
}

OS_NAME=$(detect_os)
log "Detected OS: ${OS_NAME}"

case "$OS_NAME" in
  Linux)
    bash "$SCRIPT_DIR/install_deps_linux.sh"
    ;;
  Darwin)
    bash "$SCRIPT_DIR/install_deps_macos.sh"
    ;;
  Windows)
    pwsh "$SCRIPT_DIR/install_deps_windows.ps1"
    ;;
  *)
    log "Unsupported OS. Please install dependencies manually."
    exit 1
    ;;
 esac

log "Installing Python dependencies (if requirements.txt present)"
if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
  if command -v python3 >/dev/null 2>&1; then
    python3 -m venv "$PROJECT_ROOT/.venv" 2>/dev/null || true
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/.venv/bin/activate"
    pip install --upgrade pip
    pip install -r "$PROJECT_ROOT/requirements.txt"
  else
    log "python3 not found on PATH; install python before continuing."
  fi
fi

log "Installing frontend dependencies"
if [ -d "$PROJECT_ROOT/frontend/prophet-labs-console" ]; then
  pushd "$PROJECT_ROOT/frontend/prophet-labs-console" >/dev/null
  if command -v npm >/dev/null 2>&1; then
    if [ -f package-lock.json ]; then
      npm install
    elif [ -f yarn.lock ] && command -v yarn >/dev/null 2>&1; then
      yarn install
    else
      npm install
    fi
  else
    log "npm not available; skip frontend dependency install."
  fi
  popd >/dev/null
fi

log "Dependency installation complete."
