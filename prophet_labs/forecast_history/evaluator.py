"""Evaluate issued forecasts against realized values."""
from __future__ import annotations

import datetime as dt
from collections import defaultdict
from typing import Dict, Iterable, Optional

from prophet_labs.forecast_history.config import AccuracyToleranceConfig
from prophet_labs.forecast_history.models import ForecastEvaluation
from prophet_labs.forecast_history.repository import ForecastHistoryRepository
from prophet_labs.utils.logging_config import get_logger

LOGGER = get_logger("prophet_labs.accuracy")


def evaluate_pending_forecasts(
    repo: Optional[ForecastHistoryRepository] = None,
    tolerance_config: Optional[AccuracyToleranceConfig] = None,
    metrics: Optional[Iterable[str]] = None,
) -> Dict[str, Dict[str, int]]:
    """Evaluate pending forecasts that now have realized values.

    Returns a summary mapping per metric with counts of evaluated and skipped items.
    """

    repository = repo or ForecastHistoryRepository()
    tolerance_cfg = tolerance_config or AccuracyToleranceConfig()
    metric_filter = set(metrics) if metrics else None

    pending = repository.pending_forecasts(metric_id=None, upto=None)
    summary: Dict[str, Dict[str, int]] = defaultdict(lambda: {"evaluated": 0, "skipped": 0})

    for forecast in pending:
        if metric_filter and forecast.metric_id not in metric_filter:
            summary[forecast.metric_id]["skipped"] += 1
            continue

        latest_actual_ts = repository.latest_observation_timestamp(forecast.metric_id)
        if latest_actual_ts is None or latest_actual_ts < forecast.target_time:
            summary[forecast.metric_id]["skipped"] += 1
            continue

        actual_value = repository.observation_value_at(forecast.metric_id, forecast.target_time)
        if actual_value is None:
            LOGGER.warning(
                "Missing actual value for forecast evaluation",
                extra_fields={"metric_id": forecast.metric_id, "target_time": forecast.target_time.isoformat()},
            )
            summary[forecast.metric_id]["skipped"] += 1
            continue

        tolerance = tolerance_cfg.tolerance_for(forecast.metric_id)
        error = actual_value - forecast.yhat
        relative_error = abs(error) / max(abs(actual_value), 1e-9)

        within_tolerance = False
        tolerance_used: Optional[float] = None
        if tolerance.tolerance_abs is not None:
            within_tolerance = abs(error) <= tolerance.tolerance_abs
            tolerance_used = tolerance.tolerance_abs
        elif tolerance.tolerance_rel is not None:
            within_tolerance = relative_error <= tolerance.tolerance_rel
            tolerance_used = tolerance.tolerance_rel

        evaluation = ForecastEvaluation(
            forecast_id=forecast.id,
            metric_id=forecast.metric_id,
            target_time=forecast.target_time,
            actual_value=actual_value,
            error=error,
            relative_error=relative_error,
            within_tolerance=within_tolerance,
            happened=within_tolerance,
            tolerance_used=tolerance_used,
            evaluated_at=dt.datetime.utcnow(),
        )

        repository.save_evaluation(forecast.id, evaluation)
        summary[forecast.metric_id]["evaluated"] += 1

    LOGGER.info("Forecast evaluation summary", extra_fields={"summary": summary})
    return summary


__all__ = ["evaluate_pending_forecasts"]
