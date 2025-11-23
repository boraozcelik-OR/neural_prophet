#!/usr/bin/env bash
set -euo pipefail

log() { echo "[linux] $1"; }

PKG_MANAGER=""
if command -v apt-get >/dev/null 2>&1; then
  PKG_MANAGER="apt-get"
elif command -v yum >/dev/null 2>&1; then
  PKG_MANAGER="yum"
elif command -v dnf >/dev/null 2>&1; then
  PKG_MANAGER="dnf"
elif command -v pacman >/dev/null 2>&1; then
  PKG_MANAGER="pacman"
fi

if [ -z "$PKG_MANAGER" ]; then
  log "No supported package manager found. Install dependencies manually."
  exit 0
fi

log "Using package manager: $PKG_MANAGER"

install_pkg() {
  pkg=$1
  if command -v "$pkg" >/dev/null 2>&1; then
    log "$pkg already installed"
    return
  fi
  case "$PKG_MANAGER" in
    apt-get)
      sudo apt-get update -y
      sudo apt-get install -y "$pkg"
      ;;
    yum)
      sudo yum install -y "$pkg"
      ;;
    dnf)
      sudo dnf install -y "$pkg"
      ;;
    pacman)
      sudo pacman -Sy --noconfirm "$pkg"
      ;;
  esac
}

install_pkg python3
install_pkg python3-venv || true
install_pkg nodejs || true
install_pkg npm || true
install_pkg git || true
install_pkg redis-server || install_pkg redis || true
install_pkg postgresql || true
install_pkg build-essential || install_pkg gcc || true

log "Linux dependency installation complete"
