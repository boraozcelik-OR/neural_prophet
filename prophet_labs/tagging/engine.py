"""Tagging engine that applies thresholds across metrics."""
from __future__ import annotations

from typing import Dict, List

import pandas as pd

from prophet_labs.config.settings import load_thresholds
from prophet_labs.tagging.rules import TagResult, apply_thresholds


class TaggingEngine:
    def __init__(self, thresholds: Dict[str, Dict[str, float]] | None = None):
        self.thresholds = thresholds or load_thresholds()

    def tag_row(self, metric_id: str, value: float) -> TagResult:
        metric_thresholds = self.thresholds.get(metric_id, {})
        return apply_thresholds(value, metric_thresholds)

    def tag_dataframe(self, df: pd.DataFrame, value_col: str = "value") -> pd.DataFrame:
        results: List[TagResult] = []
        for _, row in df.iterrows():
            result = self.tag_row(row["metric_id"], row[value_col])
            results.append(result)
        df = df.copy()
        df["status"] = [r.status for r in results]
        df["rationale"] = [r.rationale for r in results]
        return df


__all__ = ["TaggingEngine"]
