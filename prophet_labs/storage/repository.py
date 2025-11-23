"""Repository and session management for Prophet Labs."""
from __future__ import annotations

import contextlib
import datetime as dt
from typing import Iterable, List, Optional, Sequence

from sqlalchemy import create_engine, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from prophet_labs.config.settings import ProphetLabsSettings, get_settings
from prophet_labs.storage.models import (
    Base,
    MetricDefinition,
    MetricForecast,
    MetricObservation,
    ModelRun,
    Report,
)
from prophet_labs.utils.logging import get_logger

LOGGER = get_logger(__name__)


class Repository:
    def __init__(self, settings: Optional[ProphetLabsSettings] = None, engine: Optional[Engine] = None):
        self.settings = settings or get_settings()
        self.engine = engine or create_engine(self.settings.database_url, future=True)
        Base.metadata.create_all(self.engine)
        self._session_factory = sessionmaker(self.engine, expire_on_commit=False, future=True)

    @contextlib.contextmanager
    def session(self) -> Iterable[Session]:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as exc:
            session.rollback()
            LOGGER.exception("Database error", exc_info=exc)
            raise
        finally:
            session.close()

    # Metric definitions
    def upsert_metric_definition(self, definition: MetricDefinition) -> MetricDefinition:
        with self.session() as session:
            existing = session.get(MetricDefinition, definition.metric_id)
            if existing:
                for field in ["name", "category", "jurisdiction", "unit", "description", "metadata_json"]:
                    setattr(existing, field, getattr(definition, field))
                session.add(existing)
                return existing
            session.add(definition)
            return definition

    def list_metric_definitions(self) -> List[MetricDefinition]:
        with self.session() as session:
            return session.execute(select(MetricDefinition)).scalars().all()

    def get_metric_definition(self, metric_id: str) -> Optional[MetricDefinition]:
        with self.session() as session:
            return session.get(MetricDefinition, metric_id)

    # Observations
    def add_observations(self, metric_id: str, observations: Sequence[MetricObservation]) -> int:
        with self.session() as session:
            metric = session.get(MetricDefinition, metric_id)
            if metric is None:
                raise ValueError(f"Metric {metric_id} not defined")
            for obs in observations:
                obs.metric_id = metric_id
                session.add(obs)
            return len(observations)

    def get_observations(self, metric_id: str, start: Optional[dt.date] = None, end: Optional[dt.date] = None, limit: int = 500) -> List[MetricObservation]:
        stmt = select(MetricObservation).where(MetricObservation.metric_id == metric_id)
        if start:
            stmt = stmt.where(MetricObservation.ds >= start)
        if end:
            stmt = stmt.where(MetricObservation.ds <= end)
        stmt = stmt.order_by(MetricObservation.ds.desc()).limit(limit)
        with self.session() as session:
            return session.execute(stmt).scalars().all()

    # Forecasts
    def store_forecasts(self, metric_id: str, forecasts: Sequence[MetricForecast]) -> int:
        with self.session() as session:
            for forecast in forecasts:
                forecast.metric_id = metric_id
                session.add(forecast)
            return len(forecasts)

    def latest_forecasts(self, metric_id: str, limit: int = 100) -> List[MetricForecast]:
        stmt = (
            select(MetricForecast)
            .where(MetricForecast.metric_id == metric_id)
            .order_by(MetricForecast.ds.desc())
            .limit(limit)
        )
        with self.session() as session:
            return session.execute(stmt).scalars().all()

    # Model runs
    def start_model_run(self, metric_id: str, run_type: str, parameters: Optional[dict] = None) -> ModelRun:
        run = ModelRun(metric_id=metric_id, run_type=run_type, status="running", parameters=parameters or {})
        with self.session() as session:
            session.add(run)
            session.flush()
            return run

    def complete_model_run(self, run_id: int, status: str, metrics: Optional[dict] = None, message: Optional[str] = None) -> ModelRun:
        with self.session() as session:
            run = session.get(ModelRun, run_id)
            if run is None:
                raise ValueError(f"ModelRun {run_id} not found")
            run.status = status
            run.completed_at = dt.datetime.utcnow()
            run.metrics = metrics
            run.message = message
            session.add(run)
            return run

    # Reports
    def save_report(self, report: Report) -> Report:
        with self.session() as session:
            session.add(report)
            session.flush()
            return report

    def list_reports(self, limit: int = 50) -> List[Report]:
        stmt = select(Report).order_by(Report.report_date.desc()).limit(limit)
        with self.session() as session:
            return session.execute(stmt).scalars().all()

    def get_report(self, report_id: int) -> Optional[Report]:
        with self.session() as session:
            return session.get(Report, report_id)

    # Dashboard helpers
    def metric_latest_value(self, metric_id: str) -> Optional[float]:
        stmt = (
            select(MetricObservation.value)
            .where(MetricObservation.metric_id == metric_id)
            .order_by(MetricObservation.ds.desc())
            .limit(1)
        )
        with self.session() as session:
            result = session.execute(stmt).scalar_one_or_none()
            return result

    def category_summary(self) -> List[dict]:
        stmt = (
            select(MetricDefinition.category, func.count(MetricObservation.id))
            .join(MetricObservation, MetricObservation.metric_id == MetricDefinition.metric_id)
            .group_by(MetricDefinition.category)
        )
        with self.session() as session:
            rows = session.execute(stmt).all()
            return [
                {"category": row[0], "observation_count": row[1]} for row in rows
            ]


DataRepository = Repository


__all__ = ["Repository", "DataRepository"]
