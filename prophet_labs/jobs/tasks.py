"""Domain-specific scheduled tasks for Prophet Labs."""
from __future__ import annotations

from typing import Optional

from prophet_labs.config.settings import ProphetLabsSettings, get_settings, load_sources
from prophet_labs.data_ingestion.pipeline import build_sources, run_sources
from prophet_labs.data_ingestion.sources.example_abs_source import ExampleABSSource
from prophet_labs.data_ingestion.sources.example_csv_source import ExampleCSVSource
from prophet_labs.modelling.training import train_metric_models
from prophet_labs.reports.generator import generate_daily_report
from prophet_labs.storage.repository import Repository
from prophet_labs.utils.logging import get_logger

LOGGER = get_logger(__name__)


def refresh_data(settings: Optional[ProphetLabsSettings] = None) -> int:
    settings = settings or get_settings()
    repository = Repository(settings=settings)
    factory = {
        "abs_mock": ExampleABSSource,
        "csv_mock": ExampleCSVSource,
    }
    sources = build_sources(load_sources(), factory=factory)
    df = run_sources(sources, repository)
    LOGGER.info("Scheduled ingest finished", extra={"records": len(df)})
    return len(df)


def train_all_models(settings: Optional[ProphetLabsSettings] = None) -> None:
    settings = settings or get_settings()
    repository = Repository(settings=settings)
    LOGGER.info("Starting scheduled training run")
    train_metric_models(repository=repository)


def generate_daily_reports(settings: Optional[ProphetLabsSettings] = None) -> str:
    settings = settings or get_settings()
    repository = Repository(settings=settings)
    report = generate_daily_report(repository=repository, settings=settings)
    LOGGER.info("Generated daily report", extra={"report_path": getattr(report, "path", None)})
    return getattr(report, "path", "")


__all__ = ["refresh_data", "train_all_models", "generate_daily_reports"]
