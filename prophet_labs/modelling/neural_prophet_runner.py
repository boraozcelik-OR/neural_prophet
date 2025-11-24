"""Helpers for training and forecasting using NeuralProphet."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
from neuralprophet import NeuralProphet

from prophet_labs.utils.logging import get_logger

LOGGER = get_logger(__name__)


def train_model(df: pd.DataFrame, config: Dict[str, object] | None = None) -> Tuple[NeuralProphet, pd.DataFrame]:
    config = config or {}
    model = NeuralProphet(**config)
    metrics = model.fit(df, freq=config.get("freq", "D"))
    LOGGER.info("Model trained", extra={"loss": metrics["Loss"][-1] if not metrics.empty else None})
    return model, metrics


def save_model(model: NeuralProphet, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(path))
    LOGGER.info("Saved model", extra={"path": str(path)})
    return path


def load_model(path: Path) -> NeuralProphet:
    model = NeuralProphet.load(str(path))
    LOGGER.info("Loaded model", extra={"path": str(path)})
    return model


def make_future(model: NeuralProphet, periods: int, df: pd.DataFrame) -> pd.DataFrame:
    future = model.make_future_dataframe(df=df, periods=periods)
    forecast = model.predict(future)
    LOGGER.info("Generated forecast", extra={"periods": periods, "rows": len(forecast)})
    return forecast


__all__ = ["train_model", "save_model", "load_model", "make_future"]
