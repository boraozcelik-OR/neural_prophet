#!/usr/bin/env bash
set -euo pipefail

log() { echo "[linux] $1"; }

PKG_MANAGER=""
if command -v apt-get >/dev/null 2>&1; then
  PKG_MANAGER="apt-get"
elif command -v dnf >/dev/null 2>&1; then
  PKG_MANAGER="dnf"
elif command -v yum >/dev/null 2>&1; then
  PKG_MANAGER="yum"
elif command -v pacman >/dev/null 2>&1; then
  PKG_MANAGER="pacman"
fi

if [ -z "$PKG_MANAGER" ]; then
  log "No supported package manager found. Install dependencies manually."
  exit 0
fi

log "Using package manager: $PKG_MANAGER"

update_once() {
  if [ "${UPDATED:-0}" -eq 0 ]; then
    case "$PKG_MANAGER" in
      apt-get) sudo apt-get update -y ;;
      dnf) sudo dnf makecache -y ;;
      yum) sudo yum makecache -y ;;
      pacman) sudo pacman -Sy --noconfirm ;;
    esac
    UPDATED=1
  fi
}

install_pkg_list() {
  update_once
  case "$PKG_MANAGER" in
    apt-get)
      sudo apt-get install -y "$@"
      ;;
    dnf)
      sudo dnf install -y "$@"
      ;;
    yum)
      sudo yum install -y "$@"
      ;;
    pacman)
      sudo pacman -S --noconfirm "$@"
      ;;
  esac
}

case "$PKG_MANAGER" in
  apt-get)
    install_pkg_list python3 python3-venv python3-pip nodejs npm git redis-server postgresql build-essential curl
    ;;
  dnf|yum)
    install_pkg_list python3 python3-virtualenv python3-pip nodejs npm git redis postgresql postgresql-server gcc make curl
    ;;
  pacman)
    install_pkg_list python python-pip nodejs npm git redis postgresql base-devel curl
    ;;
esac

log "Linux dependency installation complete"
