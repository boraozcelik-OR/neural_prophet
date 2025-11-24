"""Aggregate news articles into time-series metrics for forecasting."""
from __future__ import annotations

import datetime as dt
import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence

from prophet_labs.storage.models import MetricDefinition, MetricObservation, NewsArticle
from prophet_labs.storage.repository import Repository
from prophet_labs.utils.logging import get_logger

LOGGER = get_logger(__name__)


@dataclass
class AggregatedPoint:
    metric_id: str
    metric_name: str
    category: str
    jurisdiction: str
    ds: dt.date
    value: float
    unit: str
    metadata: Dict
    source_name: str = "NSI"
    source_url: str | None = None


class NewsAggregator:
    """Builds daily risk indexes from enriched news articles."""

    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def aggregate_daily(self, target_date: dt.date) -> int:
        articles = self.repository.get_news_articles_by_date(target_date)
        grouped = self._group_articles(articles)
        points = [self._compute_point(target_date, key, items) for key, items in grouped.items()]
        self._persist(points)
        return len(points)

    def _group_articles(self, articles: Iterable[NewsArticle]) -> Dict[str, List[NewsArticle]]:
        grouped: Dict[str, List[NewsArticle]] = defaultdict(list)
        for article in articles:
            domains: Sequence[str] = article.nsi.get("political_domain", []) if article.nsi else []
            domains = domains or ["general"]
            for domain in domains:
                key = f"{domain}|{article.source_type}"
                grouped[key].append(article)
        return grouped

    def _compute_point(self, target_date: dt.date, key: str, articles: Sequence[NewsArticle]) -> AggregatedPoint:
        domain, source_type = key.split("|")
        risk_scores = [a.nsi.get("risk_score", 0.0) for a in articles if a.nsi]
        sentiments = [a.nsi.get("sentiment", {}).get("polarity", 0.0) for a in articles if a.nsi]
        risk_avg = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
        sentiment_avg = sum(sentiments) / len(sentiments) if sentiments else 0.0
        intensity = self._intensity_index(risk_avg, len(articles), sentiment_avg)
        metric_id = f"news_{domain}_risk_{source_type}"
        name = f"News Risk – {domain.replace('_', ' ').title()} ({source_type.replace('_', ' ').title()})"
        return AggregatedPoint(
            metric_id=metric_id,
            metric_name=name,
            category="news_politics",
            jurisdiction="AU",
            ds=target_date,
            value=intensity,
            unit="index",
            metadata={"topic": domain, "source_type": source_type, "article_count": len(articles)},
        )

    @staticmethod
    def _intensity_index(risk_avg: float, count: int, sentiment_avg: float) -> float:
        return float(1 / (1 + math.exp(-(1.5 * risk_avg + 0.3 * math.log1p(count) + 0.2 * abs(sentiment_avg)))))

    def _persist(self, points: Sequence[AggregatedPoint]) -> None:
        for point in points:
            self.repository.upsert_metric_definition(
                MetricDefinition(
                    metric_id=point.metric_id,
                    name=point.metric_name,
                    category=point.category,
                    jurisdiction=point.jurisdiction,
                    unit=point.unit,
                    description="News risk index aggregated from NSI feeds",
                    metadata_json=point.metadata,
                )
            )
            obs = MetricObservation(
                metric_id=point.metric_id,
                ds=point.ds,
                value=point.value,
                source_name=point.source_name,
                source_url=point.source_url,
                metadata_json=point.metadata,
            )
            self.repository.add_observations(point.metric_id, [obs])


__all__ = ["NewsAggregator", "AggregatedPoint"]
