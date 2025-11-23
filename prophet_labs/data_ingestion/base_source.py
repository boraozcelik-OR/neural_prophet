"""Abstract interfaces for Prophet Labs data ingestion sources."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List

import pandas as pd


class BaseSource(ABC):
    """Base class for ingesting external data into the normalized schema."""

    def __init__(self, source_name: str, metrics: List[str], options: Dict[str, object] | None = None):
        self.source_name = source_name
        self.metrics = metrics
        self.options = options or {}

    @abstractmethod
    def fetch_raw_data(self) -> pd.DataFrame:
        """Retrieve raw data from the upstream system."""

    @abstractmethod
    def transform(self, raw: pd.DataFrame) -> pd.DataFrame:
        """Transform raw data into the Prophet Labs normalized schema."""

    def run(self) -> pd.DataFrame:
        raw = self.fetch_raw_data()
        return self.transform(raw)


__all__ = ["BaseSource"]
