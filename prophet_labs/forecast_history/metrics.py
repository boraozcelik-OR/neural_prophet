"""Accuracy metric aggregation utilities."""
from __future__ import annotations

import datetime as dt
from typing import Dict, Iterable, List, Optional, Tuple

from sqlalchemy import select

from prophet_labs.forecast_history.models import ForecastEvaluation, ForecastIssued
from prophet_labs.forecast_history.repository import ForecastHistoryRepository
from prophet_labs.utils.logging_config import get_logger

LOGGER = get_logger("prophet_labs.accuracy")

DEFAULT_HORIZON_BUCKETS: List[Tuple[str, Tuple[int, Optional[int]]]] = [
    ("1-7", (1, 7)),
    ("8-30", (8, 30)),
    ("31+", (31, None)),
]


def _safe_mean(values: List[float]) -> Optional[float]:
    return sum(values) / len(values) if values else None


def compute_accuracy_summary(
    metric_id: str,
    window_days: int = 90,
    horizon_buckets: Iterable[Tuple[str, Tuple[int, Optional[int]]]] = DEFAULT_HORIZON_BUCKETS,
    repo: Optional[ForecastHistoryRepository] = None,
) -> Dict[str, object]:
    """Compute accuracy statistics for a metric over a time window."""

    repository = repo or ForecastHistoryRepository()
    cutoff = dt.datetime.utcnow() - dt.timedelta(days=window_days)

    with repository.repo.session() as session:
        stmt = (
            select(ForecastEvaluation, ForecastIssued.horizon_steps)
            .join(ForecastIssued, ForecastIssued.id == ForecastEvaluation.forecast_id)
            .where(ForecastEvaluation.metric_id == metric_id)
            .where(ForecastEvaluation.evaluated_at >= cutoff)
        )
        rows = session.execute(stmt).all()

    evaluations = [row[0] for row in rows]
    horizons = [row[1] for row in rows]

    num_forecasts = len(evaluations)
    num_correct = sum(1 for ev in evaluations if ev.happened)
    mae_values = [abs(ev.error) for ev in evaluations]
    mape_values = [abs(ev.relative_error) for ev in evaluations]

    overall = {
        "num_forecasts": num_forecasts,
        "num_correct": num_correct,
        "accuracy": (num_correct / num_forecasts) if num_forecasts else None,
        "mae": _safe_mean(mae_values),
        "mape": _safe_mean(mape_values),
    }

    by_horizon: List[Dict[str, object]] = []
    for (label, (min_h, max_h)) in horizon_buckets:
        bucket_items = [
            (ev, hz)
            for ev, hz in zip(evaluations, horizons)
            if hz is not None
            and (min_h is None or hz >= min_h)
            and (max_h is None or hz <= max_h)
        ]
        bucket_evals = [ev for ev, _ in bucket_items]
        bucket_num = len(bucket_evals)
        bucket_correct = sum(1 for ev in bucket_evals if ev.happened)
        by_horizon.append(
            {
                "horizon_range": label,
                "num_forecasts": bucket_num,
                "num_correct": bucket_correct,
                "accuracy": (bucket_correct / bucket_num) if bucket_num else None,
                "mae": _safe_mean([abs(ev.error) for ev in bucket_evals]),
                "mape": _safe_mean([abs(ev.relative_error) for ev in bucket_evals]),
            }
        )

    LOGGER.info(
        "Computed accuracy summary",
        extra_fields={
            "metric_id": metric_id,
            "window_days": window_days,
            "accuracy": overall.get("accuracy"),
        },
    )

    return {"metric_id": metric_id, "window_days": window_days, "overall": overall, "by_horizon": by_horizon}


__all__ = ["compute_accuracy_summary", "DEFAULT_HORIZON_BUCKETS"]
