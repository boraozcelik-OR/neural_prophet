"""Repository and session management for Prophet Labs."""
from __future__ import annotations

import contextlib
import datetime as dt
from typing import Iterable, List, Optional, Sequence

from sqlalchemy import create_engine, delete, func, select
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
    NewsArticle,
    Report,
)
from prophet_labs.forecast_history.models import ForecastEvaluation, ForecastIssued
from prophet_labs.utils.logging_config import get_logger

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

    # News articles
    def add_news_articles(self, articles: Sequence[NewsArticle]) -> int:
        if not articles:
            return 0
        with self.session() as session:
            for article in articles:
                existing = session.get(NewsArticle, article.news_id)
                if existing:
                    continue
                session.add(article)
            return len(articles)

    def get_news_articles_by_date(self, date_value: dt.date) -> List[NewsArticle]:
        start_dt = dt.datetime.combine(date_value, dt.time.min)
        end_dt = dt.datetime.combine(date_value, dt.time.max)
        stmt = (
            select(NewsArticle)
            .where(NewsArticle.published_at >= start_dt)
            .where(NewsArticle.published_at <= end_dt)
            .order_by(NewsArticle.published_at.asc())
        )
        with self.session() as session:
            return session.execute(stmt).scalars().all()

    def purge_old_news(self, cutoff: dt.datetime) -> int:
        stmt = delete(NewsArticle).where(NewsArticle.ingested_at < cutoff)
        with self.session() as session:
            result = session.execute(stmt)
            return result.rowcount or 0

    # Forecast history
    def record_forecasts(self, forecasts: Sequence[ForecastIssued]) -> int:
        if not forecasts:
            return 0
        with self.session() as session:
            for forecast in forecasts:
                session.add(forecast)
            return len(forecasts)

    def pending_forecasts(self, metric_id: Optional[str] = None, upto: Optional[dt.datetime] = None) -> List[ForecastIssued]:
        stmt = select(ForecastIssued).where(ForecastIssued.status == "PENDING")
        if metric_id:
            stmt = stmt.where(ForecastIssued.metric_id == metric_id)
        if upto:
            stmt = stmt.where(ForecastIssued.target_time <= upto)
        with self.session() as session:
            return session.execute(stmt).scalars().all()

    def set_evaluation(self, forecast_id: int, evaluation: ForecastEvaluation) -> ForecastEvaluation:
        with self.session() as session:
            forecast = session.get(ForecastIssued, forecast_id)
            if forecast is None:
                raise ValueError(f"Forecast {forecast_id} not found")
            session.add(evaluation)
            session.flush()
            forecast.status = "EVALUATED"
            forecast.evaluation_id = evaluation.id
            forecast.evaluation = evaluation
            session.add(forecast)
            return evaluation

    def forecast_history(
        self,
        metric_id: str,
        start: Optional[dt.datetime] = None,
        end: Optional[dt.datetime] = None,
        horizon_min: Optional[int] = None,
        horizon_max: Optional[int] = None,
        limit: int = 500,
    ) -> List[ForecastIssued]:
        stmt = select(ForecastIssued).where(ForecastIssued.metric_id == metric_id)
        if start:
            stmt = stmt.where(ForecastIssued.issued_at >= start)
        if end:
            stmt = stmt.where(ForecastIssued.issued_at <= end)
        if horizon_min:
            stmt = stmt.where(ForecastIssued.horizon_steps >= horizon_min)
        if horizon_max:
            stmt = stmt.where(ForecastIssued.horizon_steps <= horizon_max)
        stmt = stmt.order_by(ForecastIssued.issued_at.desc()).limit(limit)
        with self.session() as session:
            return session.execute(stmt).scalars().all()

    def observation_value_at(self, metric_id: str, target_time: dt.datetime) -> Optional[float]:
        target_date = target_time.date()
        stmt = (
            select(MetricObservation.value)
            .where(MetricObservation.metric_id == metric_id)
            .where(MetricObservation.ds == target_date)
            .limit(1)
        )
        with self.session() as session:
            return session.execute(stmt).scalar_one_or_none()

    def latest_observation_timestamp(self, metric_id: str) -> Optional[dt.datetime]:
        stmt = (
            select(MetricObservation.ds)
            .where(MetricObservation.metric_id == metric_id)
            .order_by(MetricObservation.ds.desc())
            .limit(1)
        )
        with self.session() as session:
            latest = session.execute(stmt).scalar_one_or_none()
            return dt.datetime.combine(latest, dt.time.min) if latest else None


DataRepository = Repository


__all__ = ["Repository", "DataRepository"]
