"""Environment diagnostics for Prophet Labs bootstrap.

This module inspects the host operating system, hardware, and key optional
services (PostgreSQL, Redis) to help the bootstrap layer pick sensible defaults
for worker counts, connection pools, and cache choices.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import socket
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class EnvironmentReport:
    """A structured view of host capabilities and available services."""

    os_name: str
    os_version: str
    distro: Optional[str]
    is_wsl: bool
    cpu_count: int
    total_memory_gb: float
    free_disk_gb: float
    has_postgres: bool
    has_redis: bool
    recommended_api_workers: int
    recommended_worker_concurrency: int
    python_version: str
    node_version: Optional[str]
    gpu_available: bool
    lan_ip: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


def _read_os_release() -> dict[str, str]:
    os_release = {}
    os_release_file = Path("/etc/os-release")
    if os_release_file.exists():
        for line in os_release_file.read_text().splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                os_release[key] = value.strip('"')
    return os_release


def detect_os() -> tuple[str, str, Optional[str], bool]:
    """Return os_name, os_version, distro, is_wsl."""
    system = platform.system()
    release = platform.release()
    distro = None
    is_wsl = "microsoft" in platform.version().lower()

    if system == "Linux":
        os_release = _read_os_release()
        distro = os_release.get("NAME")
        release = os_release.get("VERSION", release)
    elif system == "Darwin":
        distro = "macOS"
        release, _, _ = platform.mac_ver()
    elif system == "Windows":
        distro = "Windows"
    return system, release, distro, is_wsl


def _read_mem_total_gb() -> float:
    # Prefer psutil if available
    try:
        import psutil  # type: ignore

        return psutil.virtual_memory().total / (1024**3)
    except Exception:
        pass

    if os.name == "posix":
        meminfo = Path("/proc/meminfo")
        if meminfo.exists():
            for line in meminfo.read_text().splitlines():
                if line.startswith("MemTotal"):
                    parts = line.split()
                    if len(parts) >= 2:
                        kb_total = float(parts[1])
                        return kb_total / (1024 * 1024)
    return 0.0


def _detect_python_version() -> str:
    try:
        return platform.python_version()
    except Exception:
        return "unknown"


def _detect_node_version() -> Optional[str]:
    node = shutil.which("node")
    if not node:
        return None
    try:
        result = subprocess.run([node, "--version"], check=False, capture_output=True, text=True)
        version = result.stdout.strip() or result.stderr.strip()
        return version.lstrip("v") or None
    except Exception:
        return None


def _detect_gpu_available() -> bool:
    """Lightweight GPU presence check via nvidia-smi when available."""
    nvidia_smi = shutil.which("nvidia-smi")
    if not nvidia_smi:
        return False
    try:
        subprocess.run([nvidia_smi, "-L"], check=False, capture_output=True)
        return True
    except Exception:
        return False


def _disk_free_gb(path: Path) -> float:
    usage = shutil.disk_usage(path)
    return usage.free / (1024**3)


def _service_port_open(host: str, port: int, timeout: float = 0.25) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def detect_postgres() -> bool:
    # Quick heuristics: check common port then fall back to psql command check
    if _service_port_open("127.0.0.1", 5432):
        return True
    psql = shutil.which("psql")
    if psql:
        try:
            subprocess.run([psql, "--version"], check=False, capture_output=True)
            return True
        except Exception:
            return False
    return False


def detect_redis() -> bool:
    if _service_port_open("127.0.0.1", 6379):
        return True
    redis_cli = shutil.which("redis-cli")
    if redis_cli:
        try:
            subprocess.run([redis_cli, "--version"], check=False, capture_output=True)
            return True
        except Exception:
            return False
    return False


def detect_lan_ip() -> Optional[str]:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return None


def recommend_workers(cpu_count: int) -> tuple[int, int]:
    api_workers = max(1, min(8, cpu_count))
    worker_concurrency = max(1, min(16, cpu_count * 2))
    return api_workers, worker_concurrency


def generate_report() -> EnvironmentReport:
    os_name, os_version, distro, is_wsl = detect_os()
    cpu_count = os.cpu_count() or 1
    total_memory_gb = _read_mem_total_gb()
    free_disk_gb = _disk_free_gb(PROJECT_ROOT)
    has_postgres = detect_postgres()
    has_redis = detect_redis()
    api_workers, worker_concurrency = recommend_workers(cpu_count)
    lan_ip = detect_lan_ip()
    python_version = _detect_python_version()
    node_version = _detect_node_version()
    gpu_available = _detect_gpu_available()

    return EnvironmentReport(
        os_name=os_name,
        os_version=os_version,
        distro=distro,
        is_wsl=is_wsl,
        cpu_count=cpu_count,
        total_memory_gb=round(total_memory_gb, 2),
        free_disk_gb=round(free_disk_gb, 2),
        has_postgres=has_postgres,
        has_redis=has_redis,
        recommended_api_workers=api_workers,
        recommended_worker_concurrency=worker_concurrency,
        python_version=python_version,
        node_version=node_version,
        gpu_available=gpu_available,
        lan_ip=lan_ip,
    )


def main() -> None:
    report = generate_report()
    print("=== Prophet Labs Environment Diagnostics ===")
    print(json.dumps(asdict(report), indent=2))


if __name__ == "__main__":
    main()
