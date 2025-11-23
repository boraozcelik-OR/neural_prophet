"""SQLAlchemy models for forecast issuance and evaluation."""
from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from prophet_labs.storage.models import Base


class ForecastIssued(Base):
    __tablename__ = "forecast_issued"
    __table_args__ = (
        UniqueConstraint("metric_id", "issued_at", "target_time", "model_version", name="uq_forecast_unique"),
        Index("ix_forecast_issued_metric_target", "metric_id", "target_time"),
    )

    id = Column(Integer, primary_key=True)
    metric_id = Column(String(128), nullable=False)
    model_version = Column(String(128), nullable=True)
    issued_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    target_time = Column(DateTime, nullable=False)
    horizon_steps = Column(Integer, nullable=False)
    yhat = Column(Float, nullable=False)
    yhat_lower = Column(Float, nullable=True)
    yhat_upper = Column(Float, nullable=True)
    extra_info = Column(JSON, nullable=True)
    status = Column(String(32), nullable=False, default="PENDING")
    evaluation_id = Column(Integer, ForeignKey("forecast_evaluation.id"), nullable=True)

    evaluation = relationship("ForecastEvaluation", back_populates="forecast", uselist=False)


class ForecastEvaluation(Base):
    __tablename__ = "forecast_evaluation"
    __table_args__ = (
        Index("ix_forecast_eval_metric_target", "metric_id", "target_time"),
    )

    id = Column(Integer, primary_key=True)
    forecast_id = Column(Integer, ForeignKey("forecast_issued.id"), nullable=False)
    metric_id = Column(String(128), nullable=False)
    target_time = Column(DateTime, nullable=False)
    actual_value = Column(Float, nullable=False)
    error = Column(Float, nullable=False)
    relative_error = Column(Float, nullable=False)
    within_tolerance = Column(Boolean, nullable=False)
    happened = Column(Boolean, nullable=False)
    tolerance_used = Column(Float, nullable=True)
    evaluated_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)

    forecast = relationship("ForecastIssued", back_populates="evaluation")


__all__ = ["ForecastIssued", "ForecastEvaluation"]
