"""Accuracy tolerance configuration loader."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from prophet_labs.config.settings import load_accuracy_thresholds

_FALLBACK_REL = 0.05


@dataclass
class Tolerance:
    tolerance_abs: Optional[float] = None
    tolerance_rel: Optional[float] = None


class AccuracyToleranceConfig:
    """Resolve per-metric tolerance settings with sensible fallbacks."""

    def __init__(self, thresholds: Optional[Dict[str, Dict[str, float]]] = None) -> None:
        self._raw = thresholds or load_accuracy_thresholds()

    def tolerance_for(self, metric_id: str) -> Tolerance:
        entry = self._raw.get(metric_id, {}) if isinstance(self._raw, dict) else {}
        default_entry = self._raw.get("default", {}) if isinstance(self._raw, dict) else {}
        tol_abs = entry.get("tolerance_abs") or default_entry.get("tolerance_abs")
        tol_rel = entry.get("tolerance_rel") or default_entry.get("tolerance_rel") or _FALLBACK_REL
        return Tolerance(tolerance_abs=tol_abs, tolerance_rel=tol_rel)


__all__ = ["AccuracyToleranceConfig", "Tolerance"]
