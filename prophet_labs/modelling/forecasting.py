"""Forecast helpers for Prophet Labs."""
from __future__ import annotations

import datetime as dt
import hashlib
from pathlib import Path
from typing import Dict, List

import pandas as pd

from prophet_labs.forecast_history.models import ForecastIssued
from prophet_labs.forecast_history.repository import ForecastHistoryRepository
from prophet_labs.modelling.neural_prophet_runner import load_model, make_future
from prophet_labs.storage.models import MetricForecast
from prophet_labs.storage.repository import Repository
from prophet_labs.utils.logging_config import get_logger

LOGGER = get_logger("prophet_labs.forecast")


def forecast_metric(metric_id: str, history: pd.DataFrame, model_dir: Path, periods: int = 12) -> pd.DataFrame:
    model_path = model_dir.joinpath(f"{metric_id}_model.np")
    model = load_model(model_path)
    forecast = make_future(model, periods=periods, df=history)
    forecast["metric_id"] = metric_id
    LOGGER.info("Forecast generated", extra_fields={"metric_id": metric_id, "rows": len(forecast)})
    return forecast


def bulk_forecast(histories: Dict[str, pd.DataFrame], model_dir: Path, periods: int = 12) -> Dict[str, pd.DataFrame]:
    results: Dict[str, pd.DataFrame] = {}
    for metric_id, df in histories.items():
        if df.empty:
            LOGGER.warning("Skipping empty history", extra_fields={"metric_id": metric_id})
            continue
        results[metric_id] = forecast_metric(metric_id, df, model_dir, periods=periods)
    return results


def forecast_all_metrics(repository: Repository, periods: int = 12) -> None:
    history_repo = ForecastHistoryRepository(repository)
    definitions = repository.list_metric_definitions()
    for definition in definitions:
        observations = repository.get_observations(definition.metric_id, limit=10000)
        if not observations:
            LOGGER.warning("No observations for metric, skipping forecast", extra_fields={"metric_id": definition.metric_id})
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
                    yhat_lower=getattr(row, "yhat_lower", None),
                    yhat_upper=getattr(row, "yhat_upper", None),
                )
                for row in forecast_df.itertuples()
            ]
            repository.store_forecasts(definition.metric_id, forecasts)

            issued_at = dt.datetime.utcnow()
            model_version = _hash_file(repository.settings.models_path.joinpath(f"{definition.metric_id}_model.np"))
            last_actual = history["ds"].max()
            future_rows = forecast_df[forecast_df["ds"] > last_actual].reset_index(drop=True)
            issued_records: List[ForecastIssued] = []
            for idx, row in enumerate(future_rows.itertuples(), start=1):
                issued_records.append(
                    ForecastIssued(
                        metric_id=definition.metric_id,
                        model_version=model_version,
                        issued_at=issued_at,
                        target_time=dt.datetime.combine(row.ds, dt.time()),
                        horizon_steps=idx,
                        yhat=row.yhat,
                        yhat_lower=getattr(row, "yhat_lower", None),
                        yhat_upper=getattr(row, "yhat_upper", None),
                        extra_info={"periods": periods},
                    )
                )
            history_repo.record_forecasts(issued_records)
        except FileNotFoundError:
            LOGGER.warning("No trained model found; skipping forecast", extra_fields={"metric_id": definition.metric_id})
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.exception("Forecasting failed", extra_fields={"metric_id": definition.metric_id})


def _hash_file(path: Path) -> str:
    if not path.exists():
        return "unknown"
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


__all__ = ["forecast_metric", "bulk_forecast", "forecast_all_metrics"]
