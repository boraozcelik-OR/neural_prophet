"""FastAPI backend for Prophet Labs."""
from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest

from prophet_labs.config.settings import get_settings, load_categories
from prophet_labs.forecast_history.metrics import compute_accuracy_summary
from prophet_labs.forecast_history.repository import ForecastHistoryRepository
from prophet_labs.storage.repository import Repository
from prophet_labs.utils.logging_config import LoggingConfig, get_logger, init_logging

LOGGER = get_logger("prophet_labs.ui")
settings = get_settings()
init_logging(
    LoggingConfig(
        logs_dir=Path("logs"),
        rotation_type=settings.log_rotation_type,
        max_bytes=settings.log_max_bytes,
        backup_count=settings.log_backup_count,
        rotation_when=settings.log_rotation_when,
        rotation_interval=settings.log_rotation_interval,
        log_to_console=settings.log_to_console,
        default_level=settings.log_level,
        levels=settings.log_levels,
    )
)
repo = Repository(settings=settings)
forecast_repo = ForecastHistoryRepository(repo)

REQUEST_COUNTER = Counter("prophet_labs_requests_total", "API request count", ["endpoint"])
LATEST_FORECAST_GAUGE = Gauge("prophet_labs_forecast_points", "Latest forecast points cached", ["metric_id"])


class MetricDefinitionOut(BaseModel):
    metric_id: str
    name: str
    category: str
    jurisdiction: str
    unit: Optional[str]
    description: Optional[str]

    class Config:
        orm_mode = True


class ObservationOut(BaseModel):
    ds: dt.date
    value: float
    source_name: Optional[str]

    class Config:
        orm_mode = True


class ForecastOut(BaseModel):
    ds: dt.date
    yhat: float
    yhat_lower: Optional[float]
    yhat_upper: Optional[float]

    class Config:
        orm_mode = True


class ReportOut(BaseModel):
    id: int
    report_date: dt.date
    category: Optional[str]
    path: str
    content_type: str

    class Config:
        orm_mode = True


class ForecastEvaluationOut(BaseModel):
    actual_value: float
    error: float
    relative_error: float
    within_tolerance: bool
    happened: bool
    tolerance_used: Optional[float]
    evaluated_at: dt.datetime

    class Config:
        orm_mode = True


class ForecastIssuedOut(BaseModel):
    issued_at: dt.datetime
    target_time: dt.datetime
    horizon_steps: int
    yhat: float
    yhat_lower: Optional[float]
    yhat_upper: Optional[float]
    status: str
    model_version: Optional[str]
    evaluation: Optional[ForecastEvaluationOut]

    class Config:
        orm_mode = True


app = FastAPI(title="Prophet Labs API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_repository() -> Repository:
    return repo


def get_forecast_repository() -> ForecastHistoryRepository:
    return forecast_repo


@app.get("/health")
def healthcheck():
    REQUEST_COUNTER.labels(endpoint="health").inc()
    return {"status": "ok", "environment": settings.environment}


@app.get(f"{settings.api_base_path}/metrics", response_model=List[MetricDefinitionOut])
def list_metrics(repository: Repository = Depends(get_repository)):
    REQUEST_COUNTER.labels(endpoint="metrics").inc()
    return repository.list_metric_definitions()


@app.get(f"{settings.api_base_path}/metrics/categories")
def list_categories():
    REQUEST_COUNTER.labels(endpoint="categories").inc()
    return load_categories()


@app.get(f"{settings.api_base_path}/metrics/{{metric_id}}", response_model=MetricDefinitionOut)
def get_metric(metric_id: str, repository: Repository = Depends(get_repository)):
    REQUEST_COUNTER.labels(endpoint="metric_detail").inc()
    metric = repository.get_metric_definition(metric_id)
    if not metric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")
    return metric


@app.get(f"{settings.api_base_path}/metrics/{{metric_id}}/observations", response_model=List[ObservationOut])
def get_observations(
    metric_id: str,
    start: Optional[dt.date] = None,
    end: Optional[dt.date] = None,
    limit: int = 500,
    repository: Repository = Depends(get_repository),
):
    REQUEST_COUNTER.labels(endpoint="observations").inc()
    metric = repository.get_metric_definition(metric_id)
    if not metric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")
    return repository.get_observations(metric_id, start=start, end=end, limit=limit)


@app.get(f"{settings.api_base_path}/metrics/{{metric_id}}/forecast_history")
def get_forecast_history(
    metric_id: str,
    start: Optional[dt.datetime] = None,
    end: Optional[dt.datetime] = None,
    horizon_min: Optional[int] = None,
    horizon_max: Optional[int] = None,
    limit: int = 500,
    repository: ForecastHistoryRepository = Depends(get_forecast_repository),
):
    REQUEST_COUNTER.labels(endpoint="forecast_history").inc()
    records = repository.history(
        metric_id=metric_id,
        start=start,
        end=end,
        horizon_min=horizon_min,
        horizon_max=horizon_max,
        limit=limit,
    )
    return {"metric_id": metric_id, "forecasts": [ForecastIssuedOut.from_orm(rec) for rec in records]}


@app.get(f"{settings.api_base_path}/metrics/{{metric_id}}/accuracy")
def get_metric_accuracy(metric_id: str, window_days: int = 90, repository: ForecastHistoryRepository = Depends(get_forecast_repository)):
    REQUEST_COUNTER.labels(endpoint="accuracy").inc()
    summary = compute_accuracy_summary(metric_id, window_days=window_days, repo=repository)
    return summary


@app.get(f"{settings.api_base_path}/metrics/{{metric_id}}/forecast", response_model=List[ForecastOut])
def get_forecast(metric_id: str, limit: int = 100, repository: Repository = Depends(get_repository)):
    REQUEST_COUNTER.labels(endpoint="forecast").inc()
    forecasts = repository.latest_forecasts(metric_id, limit=limit)
    LATEST_FORECAST_GAUGE.labels(metric_id=metric_id).set(len(forecasts))
    return forecasts


@app.post(f"{settings.api_base_path}/jobs/refresh")
def trigger_refresh():
    REQUEST_COUNTER.labels(endpoint="jobs_refresh").inc()
    LOGGER.info("Requested data refresh job")
    return {"status": "accepted", "job": "refresh_data"}


@app.post(f"{settings.api_base_path}/jobs/train")
def trigger_train():
    REQUEST_COUNTER.labels(endpoint="jobs_train").inc()
    LOGGER.info("Requested model training job")
    return {"status": "accepted", "job": "train_models"}


@app.get(f"{settings.api_base_path}/reports", response_model=List[ReportOut])
def list_reports(repository: Repository = Depends(get_repository)):
    REQUEST_COUNTER.labels(endpoint="reports").inc()
    return repository.list_reports()


@app.get(f"{settings.api_base_path}/reports/{{report_id}}", response_model=ReportOut)
def get_report(report_id: int, repository: Repository = Depends(get_repository)):
    REQUEST_COUNTER.labels(endpoint="report_detail").inc()
    report = repository.get_report(report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return report


@app.get("/metrics")
def prometheus_metrics():
    if not settings.metrics_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metrics disabled")
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
