"""Storage abstractions for Prophet Labs."""

from prophet_labs.storage.models import NormalizedRecord
from prophet_labs.storage.repository import DataRepository

__all__ = ["NormalizedRecord", "DataRepository"]
