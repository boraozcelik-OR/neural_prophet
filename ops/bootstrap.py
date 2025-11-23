"""Prophet Labs bootstrap entrypoint.

This script orchestrates environment diagnostics, .env generation, and
suggested runtime settings for local or LAN development. It is intentionally
conservative: no destructive system tweaks are applied without explicit flags.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Dict

from ops.diagnostics import EnvironmentReport, generate_report
from ops.lan_info import format_access_urls

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"
TEMPLATE_ENV_PATH = PROJECT_ROOT / "ops" / "templates" / ".env.example"


ENV_DEFAULTS = {
    "ENVIRONMENT": "dev",
    "API_HOST": "0.0.0.0",
    "API_PORT": "8000",
    "FRONTEND_HOST": "0.0.0.0",
    "FRONTEND_PORT": "3000",
    "ENABLE_CACHING": "true",
    "ENABLE_JOBS": "true",
    "LOG_LEVEL": "INFO",
}


def _load_template_env() -> Dict[str, str]:
    defaults: Dict[str, str] = {}
    if TEMPLATE_ENV_PATH.exists():
        for line in TEMPLATE_ENV_PATH.read_text().splitlines():
            if line.strip().startswith("#") or not line.strip() or "=" not in line:
                continue
            key, value = line.split("=", 1)
            defaults[key.strip()] = value.strip()
    return defaults


def _detect_database(report: EnvironmentReport) -> str:
    if report.has_postgres:
        return "postgresql://localhost:5432/prophet_labs"
    sqlite_path = PROJECT_ROOT / "data" / "prophet_labs.db"
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{sqlite_path}"


def _detect_redis(report: EnvironmentReport) -> str:
    return "redis://localhost:6379/0" if report.has_redis else ""


def _render_env(report: EnvironmentReport, args: argparse.Namespace) -> Dict[str, str]:
    merged = {**_load_template_env(), **ENV_DEFAULTS}
    merged["ENVIRONMENT"] = args.environment
    merged["API_PORT"] = str(args.api_port)
    merged["FRONTEND_PORT"] = str(args.frontend_port)
    merged.setdefault("API_HOST", "0.0.0.0")
    merged.setdefault("FRONTEND_HOST", "0.0.0.0")
    merged.setdefault("DATABASE_URL", _detect_database(report))
    merged.setdefault("REDIS_URL", _detect_redis(report))
    merged.setdefault("ENABLE_CACHING", "true" if report.has_redis else "false")
    merged.setdefault("ENABLE_JOBS", "true")
    merged.setdefault("LOG_LEVEL", "INFO")
    merged["RECOMMENDED_API_WORKERS"] = str(report.recommended_api_workers)
    merged["RECOMMENDED_WORKER_CONCURRENCY"] = str(report.recommended_worker_concurrency)
    return merged


def _write_env(env_path: Path, values: Dict[str, str]) -> None:
    lines = [f"{k}={v}" for k, v in values.items()]
    env_path.write_text("\n".join(lines) + "\n")


def generate_env_file(env_path: Path, report: EnvironmentReport, args: argparse.Namespace) -> None:
    env_vars = _render_env(report, args)
    if env_path.exists() and not args.force:
        print(f"[skip] {env_path} already exists. Use --force to overwrite.")
        return
    _write_env(env_path, env_vars)
    print(f"[ok] Wrote environment configuration to {env_path}")


def print_summary(report: EnvironmentReport, args: argparse.Namespace) -> None:
    print("=== Prophet Labs Bootstrap Summary ===")
    print(report.to_json())
    print("\nSuggested runtime settings:")
    print(f"  API workers: {report.recommended_api_workers}")
    print(f"  Job concurrency: {report.recommended_worker_concurrency}")
    print("\nAccess URLs:")
    print(format_access_urls(api_port=args.api_port, frontend_port=args.frontend_port))
    if report.has_postgres:
        print("[info] PostgreSQL detected locally. DATABASE_URL will use it.")
    else:
        print("[info] PostgreSQL not detected. Falling back to SQLite.")
    if report.has_redis:
        print("[info] Redis detected locally. Caching and jobs can be enabled.")
    else:
        print("[warn] Redis not detected. Caching/job queue will be disabled unless configured.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap Prophet Labs environment")
    parser.add_argument("--env-path", default=DEFAULT_ENV_PATH, type=Path, help="Path to write .env")
    parser.add_argument("--environment", default="dev", choices=["dev", "stage", "prod"], help="Environment label")
    parser.add_argument("--api-port", default=8000, type=int, help="Backend API port")
    parser.add_argument("--frontend-port", default=3000, type=int, help="Frontend port")
    parser.add_argument("--force", action="store_true", help="Overwrite existing env file")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = generate_report()
    generate_env_file(args.env_path, report, args)
    print_summary(report, args)


if __name__ == "__main__":
    main()
