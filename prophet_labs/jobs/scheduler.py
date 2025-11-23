"""Simple scheduler for Prophet Labs recurring tasks."""
from __future__ import annotations

import threading
import time
from typing import Callable, List

from prophet_labs.utils.logging import get_logger

LOGGER = get_logger(__name__)


class RepeatingJob(threading.Thread):
    def __init__(self, interval_seconds: int, func: Callable, name: str = "job"):
        super().__init__(daemon=True)
        self.interval_seconds = interval_seconds
        self.func = func
        self.name = name
        self._stop_event = threading.Event()

    def run(self):
        while not self._stop_event.is_set():
            LOGGER.info("Running scheduled task", extra={"task": self.name})
            self.func()
            self._stop_event.wait(self.interval_seconds)

    def stop(self):
        self._stop_event.set()


def start_jobs(jobs: List[RepeatingJob]) -> None:
    for job in jobs:
        job.start()


__all__ = ["RepeatingJob", "start_jobs"]
