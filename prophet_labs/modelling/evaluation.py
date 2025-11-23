"""Evaluation metrics for Prophet Labs forecasts."""
from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd


def evaluate_forecast(actuals: pd.Series, forecast: pd.Series) -> Dict[str, float]:
    if actuals.empty or forecast.empty:
        return {"mae": float("nan"), "mape": float("nan")}
    mae = float(np.mean(np.abs(actuals - forecast)))
    mape = float(np.mean(np.abs((actuals - forecast) / actuals)) * 100)
    return {"mae": mae, "mape": mape}


def evaluate_dataframe(df: pd.DataFrame, actual_col: str = "y", forecast_col: str = "yhat1") -> Dict[str, float]:
    return evaluate_forecast(df[actual_col], df[forecast_col])


__all__ = ["evaluate_forecast", "evaluate_dataframe"]
