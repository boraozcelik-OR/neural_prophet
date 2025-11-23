"""Human-readable explanations for tag statuses."""
from __future__ import annotations

from typing import Dict

STATUS_EXPLANATIONS: Dict[str, str] = {
    "RED": "Off-target or high risk. Requires immediate attention.",
    "GREEN": "On track and within expected range.",
    "WHITE": "Neutral or informational status.",
    "BLACK": "Missing, invalid, or anomalous data detected.",
}


def explain_status(status: str) -> str:
    return STATUS_EXPLANATIONS.get(status, "Status unknown")


__all__ = ["STATUS_EXPLANATIONS", "explain_status"]
