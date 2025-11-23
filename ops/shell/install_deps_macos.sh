#!/usr/bin/env bash
set -euo pipefail

log() { echo "[macos] $1"; }

if ! command -v brew >/dev/null 2>&1; then
  log "Homebrew not found. Install it from https://brew.sh/ then re-run."
  exit 0
fi

log "Installing core tools via Homebrew"
brew update
brew install python node redis postgresql || true

log "macOS dependency installation complete"
