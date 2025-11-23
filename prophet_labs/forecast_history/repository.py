"""Persistence helpers for forecast issuance and evaluation."""
from __future__ import annotations

import datetime as dt
from typing import List, Optional, Sequence

from prophet_labs.storage.repository import Repository
from prophet_labs.forecast_history.models import ForecastEvaluation, ForecastIssued
from prophet_labs.utils.logging_config import get_logger

LOGGER = get_logger("prophet_labs.accuracy")


class ForecastHistoryRepository:
    """Facade over the shared Repository for forecast history operations."""

    def __init__(self, repository: Optional[Repository] = None) -> None:
        self.repo = repository or Repository()

    def record_forecasts(self, records: Sequence[ForecastIssued]) -> int:
        count = self.repo.record_forecasts(records)
        LOGGER.info(
            "Recorded forecast issuance", extra_fields={"count": count, "metric_ids": list({r.metric_id for r in records})}
        )
        return count

    def pending_forecasts(self, metric_id: Optional[str], upto: dt.datetime) -> List[ForecastIssued]:
        return self.repo.pending_forecasts(metric_id=metric_id, upto=upto)

    def save_evaluation(self, forecast_id: int, evaluation: ForecastEvaluation) -> ForecastEvaluation:
        LOGGER.debug(
            "Persisting forecast evaluation",
            extra_fields={
                "forecast_id": forecast_id,
                "metric_id": evaluation.metric_id,
                "target_time": evaluation.target_time.isoformat(),
                "happened": evaluation.happened,
            },
        )
        return self.repo.set_evaluation(forecast_id, evaluation)

    def history(
        self,
        metric_id: str,
        start: Optional[dt.datetime] = None,
        end: Optional[dt.datetime] = None,
        horizon_min: Optional[int] = None,
        horizon_max: Optional[int] = None,
        limit: int = 500,
    ) -> List[ForecastIssued]:
        return self.repo.forecast_history(
            metric_id=metric_id,
            start=start,
            end=end,
            horizon_min=horizon_min,
            horizon_max=horizon_max,
            limit=limit,
        )

    def observation_value_at(self, metric_id: str, target_time: dt.datetime) -> Optional[float]:
        return self.repo.observation_value_at(metric_id, target_time)

    def latest_observation_timestamp(self, metric_id: str) -> Optional[dt.datetime]:
        return self.repo.latest_observation_timestamp(metric_id)

