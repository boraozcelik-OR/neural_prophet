"""Prophet Labs command-line entrypoint."""
from __future__ import annotations

import argparse

from prophet_labs.config.settings import load_sources, ProphetLabsSettings
from prophet_labs.data_ingestion.pipeline import build_sources, run_sources
from prophet_labs.data_ingestion.sources.example_abs_source import ExampleABSSource
from prophet_labs.data_ingestion.sources.example_csv_source import ExampleCSVSource
from prophet_labs.storage.repository import DataRepository
from prophet_labs.utils.logging import get_logger

LOGGER = get_logger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prophet Labs CLI")
    parser.add_argument("action", choices=["ingest"], help="Action to perform")
    args = parser.parse_args()

    settings = ProphetLabsSettings()
    repository = DataRepository(settings=settings)
    factory = {
        "abs_mock": ExampleABSSource,
        "csv_mock": ExampleCSVSource,
    }
    sources = build_sources(load_sources(), factory=factory)

    if args.action == "ingest":
        df = run_sources(sources, repository)
        LOGGER.info("Ingested records", extra={"records": len(df)})


if __name__ == "__main__":
    main()
