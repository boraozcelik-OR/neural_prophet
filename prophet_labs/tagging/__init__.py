"""Traffic-light tagging for Prophet Labs metrics."""

from prophet_labs.tagging.engine import TaggingEngine
from prophet_labs.tagging.explanations import STATUS_EXPLANATIONS, explain_status
from prophet_labs.tagging.rules import TagResult, apply_thresholds

__all__ = ["TaggingEngine", "STATUS_EXPLANATIONS", "explain_status", "TagResult", "apply_thresholds"]
