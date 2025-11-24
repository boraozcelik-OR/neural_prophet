"""Report generation utilities for Prophet Labs."""
from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Dict, List

from jinja2 import Environment, FileSystemLoader
import pandas as pd

from prophet_labs.config.settings import ProphetLabsSettings
from prophet_labs.storage.models import Report
from prophet_labs.storage.repository import Repository
from prophet_labs.utils.logging import get_logger

LOGGER = get_logger(__name__)


class ReportGenerator:
    def __init__(self, settings: ProphetLabsSettings | None = None):
        self.settings = settings or ProphetLabsSettings()
        template_path = Path(__file__).parent.joinpath("templates")
        self.env = Environment(loader=FileSystemLoader(template_path))

    def render_daily(self, metrics: List[Dict[str, object]], forecast: pd.DataFrame) -> str:
        template = self.env.get_template("daily_report.html")
        return template.render(metrics=metrics, forecast=forecast.to_dict(orient="records"))

    def write_report(self, content: str, filename: str = "daily_report.html") -> Path:
        target = self.settings.outputs_path.joinpath(filename)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as handle:
            handle.write(content)
        LOGGER.info("Report written", extra={"path": str(target)})
        return target


def generate_daily_report(repository: Repository, settings: ProphetLabsSettings | None = None) -> Report:
    settings = settings or ProphetLabsSettings()
    generator = ReportGenerator(settings=settings)
    metrics_summary = repository.category_summary()
    # Placeholder forecast table
    forecast_df = pd.DataFrame()
    content = generator.render_daily(metrics_summary, forecast_df)
    path = generator.write_report(content)
    report = Report(report_date=dt.date.today(), path=str(path))
    return repository.save_report(report)


__all__ = ["ReportGenerator", "generate_daily_report"]
