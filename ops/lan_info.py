"""LAN discovery helpers for Prophet Labs bootstrap."""
from __future__ import annotations

import socket
from typing import List


def get_lan_ips() -> List[str]:
    candidates: set[str] = set()
    try:
        host_name = socket.gethostname()
        for addr in socket.getaddrinfo(host_name, None, socket.AF_INET):
            ip = addr[4][0]
            if not ip.startswith("127."):
                candidates.add(ip)
    except Exception:
        pass

    # UDP connect trick to find primary interface
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            if not ip.startswith("127."):
                candidates.add(ip)
    except Exception:
        pass

    return sorted(candidates)


def format_access_urls(api_port: int = 8000, frontend_port: int = 3000) -> str:
    ips = get_lan_ips() or ["127.0.0.1"]
    api_urls = [f"http://{ip}:{api_port}" for ip in ips]
    fe_urls = [f"http://{ip}:{frontend_port}" for ip in ips]
    return (
        "Backend URLs: " + ", ".join(api_urls) + "\n" + "Frontend URLs: " + ", ".join(fe_urls)
    )


if __name__ == "__main__":
    print(format_access_urls())
