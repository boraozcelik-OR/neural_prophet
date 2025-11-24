"""Example CSV-based source that can also synthesize fallback data."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from prophet_labs.data_ingestion.base_source import BaseSource
from prophet_labs.utils.logging import get_logger

LOGGER = get_logger(__name__)


class ExampleCSVSource(BaseSource):
    def __init__(self, source_name: str, metrics: List[str], options: Dict[str, object] | None = None):
        super().__init__(source_name, metrics, options)
        self.file_path = Path((options or {}).get("file_path", ""))
        self.jurisdiction = (options or {}).get("jurisdiction", "AU")

    def fetch_raw_data(self) -> pd.DataFrame:
        if self.file_path.exists():
            LOGGER.info("Loading CSV source", extra={"path": str(self.file_path)})
            return pd.read_csv(self.file_path, parse_dates=["ds"])

        LOGGER.warning("CSV path missing, generating synthetic health capacity data", extra={"path": str(self.file_path)})
        periods = 12
        dates = pd.date_range(end=datetime.today(), periods=periods, freq="M")
        data = {
            "ds": dates,
            "beds": np.linspace(32000, 33000, periods) + np.random.normal(0, 100, periods),
            "icu_capacity": np.linspace(2500, 2600, periods) + np.random.normal(0, 30, periods),
            "icu_occupancy": np.linspace(70, 82, periods) + np.random.normal(0, 2, periods),
        }
        return pd.DataFrame(data)

    def transform(self, raw: pd.DataFrame) -> pd.DataFrame:
        records = []
        for _, row in raw.iterrows():
            records.extend(
                [
                    {
                        "metric_id": "health_hospital_beds",
                        "metric_name": "Hospital Beds",
                        "category": "Health & Hospitals",
                        "jurisdiction": self.jurisdiction,
                        "ds": row["ds"].date(),
                        "value": float(row.get("beds")),
                        "unit": "beds",
                        "source_name": self.source_name,
                        "source_url": str(self.file_path) if self.file_path else "generated",
                        "metadata": {"frequency": "monthly"},
                    },
                    {
                        "metric_id": "health_icu_capacity",
                        "metric_name": "ICU Capacity",
                        "category": "Health & Hospitals",
                        "jurisdiction": self.jurisdiction,
                        "ds": row["ds"].date(),
                        "value": float(row.get("icu_capacity")),
                        "unit": "beds",
                        "source_name": self.source_name,
                        "source_url": str(self.file_path) if self.file_path else "generated",
                        "metadata": {"frequency": "monthly"},
                    },
                    {
                        "metric_id": "health_icu_occupancy",
                        "metric_name": "ICU Occupancy",
                        "category": "Health & Hospitals",
                        "jurisdiction": self.jurisdiction,
                        "ds": row["ds"].date(),
                        "value": float(row.get("icu_occupancy")),
                        "unit": "%",
                        "source_name": self.source_name,
                        "source_url": str(self.file_path) if self.file_path else "generated",
                        "metadata": {"frequency": "monthly"},
                    },
                ]
            )
        return pd.DataFrame(records)


__all__ = ["ExampleCSVSource"]
