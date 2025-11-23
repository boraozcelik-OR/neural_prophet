"""Traffic-light tagging rules for metrics."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class TagResult:
    status: str
    rationale: str


def apply_thresholds(value: Optional[float], thresholds: Dict[str, float]) -> TagResult:
    if value is None:
        return TagResult(status="BLACK", rationale="Missing value")

    danger_above = thresholds.get("danger_above")
    warning_above = thresholds.get("warning_above")
    warning_below = thresholds.get("warning_below")
    danger_below = thresholds.get("danger_below")

    if danger_above is not None and value >= danger_above:
        return TagResult(status="RED", rationale=f"Value {value} exceeds danger_above {danger_above}")
    if danger_below is not None and value <= danger_below:
        return TagResult(status="RED", rationale=f"Value {value} below danger_below {danger_below}")
    if warning_above is not None and value >= warning_above:
        return TagResult(status="WHITE", rationale=f"Value {value} above warning {warning_above}")
    if warning_below is not None and value <= warning_below:
        return TagResult(status="WHITE", rationale=f"Value {value} below warning {warning_below}")
    return TagResult(status="GREEN", rationale="Within healthy range")


__all__ = ["TagResult", "apply_thresholds"]
