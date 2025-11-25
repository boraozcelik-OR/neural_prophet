"""Windows-friendly launcher for Prophet Labs.

- Optional dependency installation via PowerShell installer
- Bootstrap .env with sensible defaults
- Optionally start API (uvicorn) and frontend dev server

Build as an .exe (optional) with:
    pyinstaller --onefile --name prophetlabs-launcher ops/windows_launcher.py
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INSTALL_SCRIPT = PROJECT_ROOT / "ops" / "shell" / "install_deps_windows.ps1"
FRONTEND_DIR = PROJECT_ROOT / "frontend" / "prophet-labs-console"


class LauncherError(RuntimeError):
    """Raised when a launcher step fails."""


def run(cmd: List[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, check=check)


def ensure_logs_dir() -> None:
    (PROJECT_ROOT / "logs").mkdir(parents=True, exist_ok=True)


def install_deps() -> None:
    if not INSTALL_SCRIPT.exists():
        print(f"[launcher] Installer not found at {INSTALL_SCRIPT}, skipping.")
        return
    print("[launcher] Installing dependencies via PowerShell ...")
    run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(INSTALL_SCRIPT)])


def bootstrap(env: str, api_port: int, frontend_port: int) -> None:
    print("[launcher] Rendering .env via ops.bootstrap ...")
    run([sys.executable, "-m", "ops.bootstrap", "--yes", "--environment", env, "--api-port", str(api_port), "--frontend-port", str(frontend_port)])


def start_api(api_port: int) -> subprocess.Popen:
    print(f"[launcher] Starting API on port {api_port} ...")
    return subprocess.Popen([sys.executable, "-m", "uvicorn", "prophet_labs.ui.api:app", "--host", "0.0.0.0", "--port", str(api_port)])


def start_frontend(frontend_port: int) -> subprocess.Popen:
    print(f"[launcher] Starting frontend dev server on port {frontend_port} ...")
    return subprocess.Popen(["npm", "run", "dev", "--", "--host", "--port", str(frontend_port)], cwd=FRONTEND_DIR)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prophet Labs Windows launcher")
    parser.add_argument("--skip-install", action="store_true", help="Skip dependency installation")
    parser.add_argument("--skip-bootstrap", action="store_true", help="Skip .env rendering")
    parser.add_argument("--dev", action="store_true", help="Start API and UI dev servers")
    parser.add_argument("--environment", default="dev", help="Environment label (dev|stage|prod)")
    parser.add_argument("--api-port", type=int, default=8000, help="API port")
    parser.add_argument("--frontend-port", type=int, default=3000, help="Frontend dev server port")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_logs_dir()
    print(
        f"[launcher] options install={not args.skip_install} bootstrap={not args.skip_bootstrap} "
        f"dev={args.dev} env={args.environment} api={args.api_port} ui={args.frontend_port}"
    )

    if not args.skip_install:
        install_deps()
    else:
        print("[launcher] Skipping install as requested.")

    if not args.skip_bootstrap:
        bootstrap(args.environment, args.api_port, args.frontend_port)
    else:
        print("[launcher] Skipping bootstrap as requested.")

    procs: list[subprocess.Popen] = []
    try:
        if args.dev:
            procs.append(start_api(args.api_port))
            procs.append(start_frontend(args.frontend_port))
            print("[launcher] Dev servers launched. Press Ctrl+C to stop.")
            for proc in procs:
                proc.wait()
    except KeyboardInterrupt:
        print("[launcher] Stopping processes ...")
    finally:
        for proc in procs:
            if proc.poll() is None:
                proc.terminate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
