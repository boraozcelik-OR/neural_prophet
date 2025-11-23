"""Training orchestration for Prophet Labs models."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd

from prophet_labs.modelling.neural_prophet_runner import load_model, save_model, train_model
from prophet_labs.storage.repository import Repository
from prophet_labs.utils.logging import get_logger

LOGGER = get_logger(__name__)


def train_and_store(metric_id: str, df: pd.DataFrame, model_dir: Path, config: Dict[str, object] | None = None) -> Path:
    model, metrics = train_model(df, config=config)
    target_path = model_dir.joinpath(f"{metric_id}_model.np")
    save_model(model, target_path)
    LOGGER.info("Training complete", extra={"metric_id": metric_id, "path": str(target_path), "metrics": metrics})
    return target_path


def bulk_train(datasets: Dict[str, pd.DataFrame], model_dir: Path, config: Dict[str, object] | None = None) -> Dict[str, Path]:
    model_dir.mkdir(parents=True, exist_ok=True)
    results: Dict[str, Path] = {}
    for metric_id, df in datasets.items():
        if df.empty:
            LOGGER.warning("Skipping empty dataset", extra={"metric_id": metric_id})
            continue
        results[metric_id] = train_and_store(metric_id, df, model_dir, config=config)
    return results


def load_trained_model(metric_id: str, model_dir: Path):
    path = model_dir.joinpath(f"{metric_id}_model.np")
    if not path.exists():
        raise FileNotFoundError(f"Model not found for metric {metric_id}")
    return load_model(path)


def train_metric_models(repository: Repository, config: Dict[str, object] | None = None) -> None:
    """Train models for all registered metrics using stored observations."""

    definitions = repository.list_metric_definitions()
    for definition in definitions:
        observations = repository.get_observations(definition.metric_id, limit=10000)
        if not observations:
            LOGGER.warning("No observations for metric, skipping", extra={"metric_id": definition.metric_id})
            continue
        df = pd.DataFrame([
            {"ds": obs.ds, "y": obs.value} for obs in observations
        ])
        run = repository.start_model_run(definition.metric_id, run_type="train")
        try:
            train_and_store(definition.metric_id, df, model_dir=repository.settings.models_path, config=config)
            repository.complete_model_run(run.id, status="succeeded", metrics={"records": len(df)})
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.exception("Training failed", extra={"metric_id": definition.metric_id})
            repository.complete_model_run(run.id, status="failed", message=str(exc))


__all__ = ["train_and_store", "bulk_train", "load_trained_model", "train_metric_models"]
