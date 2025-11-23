"""Data ingestion pipeline orchestrator."""
from __future__ import annotations

from typing import Dict, Iterable, List

import pandas as pd

from prophet_labs.data_ingestion.base_source import BaseSource
from prophet_labs.storage.repository import DataRepository
from prophet_labs.utils.logging import get_logger

LOGGER = get_logger(__name__)


def run_sources(sources: Iterable[BaseSource], repository: DataRepository) -> pd.DataFrame:
    """Run multiple sources and persist normalized datasets.

    Args:
        sources: Source instances to execute.
        repository: Repository handling persistence.

    Returns:
        Combined dataframe of normalized records from all sources.
    """

    frames: List[pd.DataFrame] = []
    for source in sources:
        LOGGER.info("Running source", extra={"source": source.source_name})
        normalized = source.run()
        repository.save_dataframe(normalized, source.source_name)
        frames.append(normalized)

    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True)
    LOGGER.info("Ingestion complete", extra={"records": len(combined)})
    return combined


def build_sources(source_configs: Dict[str, Dict[str, object]], factory: Dict[str, type]) -> List[BaseSource]:
    """Instantiate sources from configuration using a factory mapping."""

    instances: List[BaseSource] = []
    for source_name, cfg in source_configs.items():
        source_type = cfg.get("type")
        source_cls = factory.get(source_type)
        if source_cls is None:
            raise ValueError(f"Unsupported source type: {source_type}")
        metrics = cfg.get("metrics", [])
        options = cfg.get("options", {})
        instances.append(source_cls(source_name=source_name, metrics=metrics, options=options))
    return instances


__all__ = ["run_sources", "build_sources"]
