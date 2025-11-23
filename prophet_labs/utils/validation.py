"""Validation helpers for normalized Prophet Labs data."""
from __future__ import annotations

from typing import Iterable, List

import pandas as pd

REQUIRED_COLUMNS: List[str] = [
    "metric_id",
    "metric_name",
    "category",
    "jurisdiction",
    "ds",
    "value",
    "unit",
    "source_name",
    "source_url",
    "metadata",
]


def validate_normalized_schema(df: pd.DataFrame, required: Iterable[str] | None = None) -> None:
    required_columns = list(required) if required else REQUIRED_COLUMNS
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


__all__ = ["validate_normalized_schema", "REQUIRED_COLUMNS"]
