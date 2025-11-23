"""Mock Australian Bureau of Statistics source producing realistic sample data."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List

import numpy as np
import pandas as pd

from prophet_labs.data_ingestion.base_source import BaseSource


class ExampleABSSource(BaseSource):
    """Generate synthetic macroeconomic metrics resembling ABS quarterly data."""

    def __init__(self, source_name: str, metrics: List[str], options: Dict[str, object] | None = None):
        super().__init__(source_name, metrics, options)
        self.frequency = (options or {}).get("frequency", "quarterly")
        self.jurisdiction = (options or {}).get("jurisdiction", "AU")

    def fetch_raw_data(self) -> pd.DataFrame:
        periods = 16
        dates = pd.date_range(end=datetime.today(), periods=periods, freq="Q")
        data = {
            "ds": dates,
            "gdp": np.linspace(1500, 1700, periods) + np.random.normal(0, 10, periods),
            "gdp_growth": np.linspace(2.0, 3.0, periods) + np.random.normal(0, 0.2, periods),
            "unemployment": np.linspace(5.0, 4.0, periods) + np.random.normal(0, 0.1, periods),
        }
        return pd.DataFrame(data)

    def transform(self, raw: pd.DataFrame) -> pd.DataFrame:
        records = []
        for _, row in raw.iterrows():
            records.extend(
                [
                    {
                        "metric_id": "economy_gdp_real",
                        "metric_name": "Real GDP",
                        "category": "Economy",
                        "jurisdiction": self.jurisdiction,
                        "ds": row["ds"].date(),
                        "value": float(row["gdp"]),
                        "unit": "Billion AUD",
                        "source_name": self.source_name,
                        "source_url": "https://www.abs.gov.au/",
                        "metadata": {"frequency": self.frequency},
                    },
                    {
                        "metric_id": "economy_gdp_growth",
                        "metric_name": "GDP Growth",
                        "category": "Economy",
                        "jurisdiction": self.jurisdiction,
                        "ds": row["ds"].date(),
                        "value": float(row["gdp_growth"]),
                        "unit": "%",
                        "source_name": self.source_name,
                        "source_url": "https://www.abs.gov.au/",
                        "metadata": {"frequency": self.frequency},
                    },
                    {
                        "metric_id": "economy_unemployment_rate",
                        "metric_name": "Unemployment Rate",
                        "category": "Economy",
                        "jurisdiction": self.jurisdiction,
                        "ds": row["ds"].date(),
                        "value": float(row["unemployment"]),
                        "unit": "%",
                        "source_name": self.source_name,
                        "source_url": "https://www.abs.gov.au/",
                        "metadata": {"frequency": self.frequency},
                    },
                ]
            )
        return pd.DataFrame(records)


__all__ = ["ExampleABSSource"]
