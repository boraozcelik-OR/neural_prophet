"""Time utilities for Prophet Labs."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

import pandas as pd


def infer_frequency(df: pd.DataFrame, column: str = "ds") -> Literal["A", "Q", "M", "D", "H"]:
    """Infer frequency from a datetime column using pandas."""

    if column not in df:
        raise KeyError(f"Column {column} not found in dataframe")
    inferred = pd.infer_freq(pd.to_datetime(df[column]))
    if inferred is None:
        return "D"
    return inferred[0]


def now_utc() -> datetime:
    return datetime.utcnow()


__all__ = ["infer_frequency", "now_utc"]
