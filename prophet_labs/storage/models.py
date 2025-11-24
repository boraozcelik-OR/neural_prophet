"""SQLAlchemy models for Prophet Labs storage layer."""
from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, Column, Date, DateTime, Float, ForeignKey, Index, Integer, MetaData, String, Text
from sqlalchemy.orm import declarative_base, relationship

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
metadata = MetaData(naming_convention=NAMING_CONVENTION)
Base = declarative_base(metadata=metadata)


class MetricDefinition(Base):
    __tablename__ = "metric_definitions"

    metric_id = Column(String(128), primary_key=True)
    name = Column(String(255), nullable=False)
    category = Column(String(64), nullable=False)
    jurisdiction = Column(String(32), nullable=False, default="AU")
    unit = Column(String(64), nullable=True)
    description = Column(Text, nullable=True)
    metadata_json = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)

    observations = relationship("MetricObservation", back_populates="metric", cascade="all, delete-orphan")
    forecasts = relationship("MetricForecast", back_populates="metric", cascade="all, delete-orphan")
    runs = relationship("ModelRun", back_populates="metric", cascade="all, delete-orphan")


class MetricObservation(Base):
    __tablename__ = "metric_observations"
    __table_args__ = (
        Index("ix_metric_observations_metric_ds", "metric_id", "ds"),
    )

    id = Column(Integer, primary_key=True)
    metric_id = Column(String(128), ForeignKey("metric_definitions.metric_id"), nullable=False)
    ds = Column(Date, nullable=False)
    value = Column(Float, nullable=False)
    source_name = Column(String(128), nullable=True)
    source_url = Column(String(512), nullable=True)
    metadata_json = Column("metadata", JSON, nullable=True)

    metric = relationship("MetricDefinition", back_populates="observations")


class ModelRun(Base):
    __tablename__ = "model_runs"

    id = Column(Integer, primary_key=True)
    metric_id = Column(String(128), ForeignKey("metric_definitions.metric_id"), nullable=False)
    run_type = Column(String(32), nullable=False)  # train|forecast|evaluation
    status = Column(String(32), nullable=False, default="pending")
    started_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    parameters = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)
    message = Column(Text, nullable=True)

    metric = relationship("MetricDefinition", back_populates="runs")
    forecasts = relationship("MetricForecast", back_populates="model_run")


class MetricForecast(Base):
    __tablename__ = "metric_forecasts"
    __table_args__ = (
        Index("ix_metric_forecasts_metric_ds", "metric_id", "ds"),
    )

    id = Column(Integer, primary_key=True)
    metric_id = Column(String(128), ForeignKey("metric_definitions.metric_id"), nullable=False)
    model_run_id = Column(Integer, ForeignKey("model_runs.id"), nullable=True)
    ds = Column(Date, nullable=False)
    yhat = Column(Float, nullable=False)
    yhat_lower = Column(Float, nullable=True)
    yhat_upper = Column(Float, nullable=True)
    metadata_json = Column("metadata", JSON, nullable=True)

    metric = relationship("MetricDefinition", back_populates="forecasts")
    model_run = relationship("ModelRun", back_populates="forecasts")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    report_date = Column(Date, default=dt.date.today, nullable=False)
    category = Column(String(64), nullable=True)
    path = Column(String(512), nullable=False)
    content_type = Column(String(128), default="text/html", nullable=False)
    metadata_json = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)


__all__ = [
    "Base",
    "MetricDefinition",
    "MetricObservation",
    "MetricForecast",
    "ModelRun",
    "Report",
    "NewsArticle",
]


class NewsArticle(Base):
    __tablename__ = "news_articles"
    __table_args__ = (
        Index("ix_news_articles_published", "published_at"),
        Index("ix_news_articles_source", "source_id", "source_type"),
    )

    news_id = Column(String(128), primary_key=True)
    source_id = Column(String(128), nullable=False)
    source_type = Column(String(32), nullable=False)
    feed_url = Column(String(512), nullable=False)
    published_at = Column(DateTime, nullable=True)
    ingested_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    title = Column(String(512), nullable=True)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    language = Column(String(16), nullable=True)
    link = Column(String(512), nullable=True)
    tags_raw = Column(JSON, nullable=True)
    metadata_json = Column("metadata", JSON, nullable=True)
    nsi = Column(JSON, nullable=True)
