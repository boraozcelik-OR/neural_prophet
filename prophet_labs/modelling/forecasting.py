"""Forecast helpers for Prophet Labs."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd

from prophet_labs.modelling.neural_prophet_runner import load_model, make_future
from prophet_labs.storage.models import MetricForecast
from prophet_labs.storage.repository import Repository
from prophet_labs.utils.logging import get_logger

LOGGER = get_logger(__name__)


def forecast_metric(metric_id: str, history: pd.DataFrame, model_dir: Path, periods: int = 12) -> pd.DataFrame:
    model_path = model_dir.joinpath(f"{metric_id}_model.np")
    model = load_model(model_path)
    forecast = make_future(model, periods=periods, df=history)
    forecast["metric_id"] = metric_id
    LOGGER.info("Forecast generated", extra={"metric_id": metric_id, "rows": len(forecast)})
    return forecast


def bulk_forecast(histories: Dict[str, pd.DataFrame], model_dir: Path, periods: int = 12) -> Dict[str, pd.DataFrame]:
    results: Dict[str, pd.DataFrame] = {}
    for metric_id, df in histories.items():
        if df.empty:
            LOGGER.warning("Skipping empty history", extra={"metric_id": metric_id})
            continue
        results[metric_id] = forecast_metric(metric_id, df, model_dir, periods=periods)
    return results


def forecast_all_metrics(repository: Repository, periods: int = 12) -> None:
    definitions = repository.list_metric_definitions()
    for definition in definitions:
        observations = repository.get_observations(definition.metric_id, limit=10000)
        if not observations:
            LOGGER.warning("No observations for metric, skipping forecast", extra={"metric_id": definition.metric_id})
            continue
        history = pd.DataFrame({
            "ds": [o.ds for o in observations],
            "y": [o.value for o in observations],
        })
        try:
            forecast_df = forecast_metric(definition.metric_id, history, model_dir=repository.settings.models_path, periods=periods)
            forecasts = [
                MetricForecast(
                    metric_id=definition.metric_id,
                    ds=row.ds,
                    yhat=row.yhat,
                    yhat_lower=row.get("yhat_lower"),
                    yhat_upper=row.get("yhat_upper"),
                )
                for row in forecast_df.itertuples()
            ]
            repository.store_forecasts(definition.metric_id, forecasts)
        except FileNotFoundError:
            LOGGER.warning("No trained model found; skipping forecast", extra={"metric_id": definition.metric_id})
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.exception("Forecasting failed", extra={"metric_id": definition.metric_id})


__all__ = ["forecast_metric", "bulk_forecast", "forecast_all_metrics"]
