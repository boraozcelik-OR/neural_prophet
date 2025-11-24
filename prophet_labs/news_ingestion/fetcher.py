"""Orchestrates news feed ingestion and enrichment."""
from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from prophet_labs.config.settings import ProphetLabsSettings, get_settings
from prophet_labs.news_ingestion.nsi_pipeline import EnrichedArticle, NsiPipeline
from prophet_labs.news_ingestion.rss_client import FeedEntry, FeedState, RssClient
from prophet_labs.storage.repository import Repository
from prophet_labs.storage.models import NewsArticle
from prophet_labs.utils.logging import get_logger

LOGGER = get_logger(__name__)


class NewsFetcher:
    """Fetch news articles from configured feeds and persist normalized records."""

    def __init__(
        self,
        settings: Optional[ProphetLabsSettings] = None,
        repository: Optional[Repository] = None,
        rss_client: Optional[RssClient] = None,
        pipeline: Optional[NsiPipeline] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.repository = repository or Repository(self.settings)
        feeds_path = self.settings.resolved_path(self.settings.news_feeds_path)
        self.feed_configs = self._load_feeds(feeds_path)
        self.rss_client = rss_client or RssClient()
        nlp_cfg = self.settings.resolved_path(self.settings.news_nlp_config)
        self.pipeline = pipeline or NsiPipeline(str(nlp_cfg))
        self.pipeline.languages = self.settings.news_languages or self.pipeline.languages
        self.state: Dict[str, FeedState] = {}

    def _load_feeds(self, path: Path) -> List[Dict]:
        if not path.exists():
            raise FileNotFoundError(f"Feed config not found: {path}")
        with path.open("r", encoding="utf-8") as handle:
            config = yaml.safe_load(handle) or {}
        return [feed for feed in config.get("feeds", []) if feed.get("enabled", True)]

    def ingest_once(self) -> int:
        """Fetch and persist articles from all configured feeds."""

        saved = 0
        for feed in self.feed_configs:
            feed_id = feed["id"]
            feed_url = feed["url"]
            source_type = feed.get("type", "surface_web")
            jurisdiction = feed.get("jurisdiction", "GLOBAL")
            category = feed.get("category", "news")
            LOGGER.info("Fetching feed", extra={"feed_id": feed_id, "url": feed_url, "source_type": source_type})
            try:
                entries, state = self.rss_client.fetch(feed_url, feed_id, source_type, self.state.get(feed_id))
                self.state[feed_id] = state
            except Exception as exc:  # pragma: no cover - network failures are expected to be rare in tests
                LOGGER.warning("Feed fetch failed", extra={"feed_id": feed_id, "error": str(exc)})
                continue

            normalized = [self._normalize(entry, jurisdiction, category) for entry in entries]
            enriched: List[EnrichedArticle] = []
            for item in normalized:
                enriched_article = self.pipeline.enrich(item)
                if enriched_article:
                    enriched.append(enriched_article)
            saved += self.repository.add_news_articles(self._to_models(enriched))
        self._apply_retention()
        return saved

    def _normalize(self, entry: FeedEntry, jurisdiction: str, category: str) -> Dict:
        return {
            "news_id": entry.news_id,
            "source_id": entry.source_id,
            "source_type": entry.source_type,
            "feed_url": entry.feed_url,
            "title": entry.title,
            "summary": entry.summary,
            "content": entry.summary,
            "language": "unknown",
            "link": entry.link,
            "published_at": entry.published_at,
            "tags": entry.tags,
            "jurisdiction": jurisdiction,
            "category": category,
        }

    def _to_models(self, articles: List[EnrichedArticle]) -> List[NewsArticle]:
        models: List[NewsArticle] = []
        now = dt.datetime.utcnow()
        for article in articles:
            models.append(
                NewsArticle(
                    news_id=article.news_id,
                    source_id=article.source_id,
                    source_type=article.source_type,
                    feed_url=article.feed_url,
                    published_at=article.published_at,
                    ingested_at=now,
                    title=article.title,
                    summary=article.summary,
                    content=article.content,
                    language=article.language,
                    link=article.link,
                    tags_raw=article.tags_raw,
                    metadata_json=article.metadata,
                    nsi={
                        "topics": article.topics,
                        "entities": article.entities,
                        "sentiment": {
                            "polarity": article.sentiment.polarity,
                            "subjectivity": article.sentiment.subjectivity,
                        },
                        "risk_score": article.risk_score,
                        "political_domain": article.political_domains,
                    },
                )
            )
        return models

    def _apply_retention(self) -> None:
        days = self.settings.news_retention_days
        if days <= 0:
            return
        cutoff = dt.datetime.utcnow() - dt.timedelta(days=days)
        deleted = self.repository.purge_old_news(cutoff)
        if deleted:
            LOGGER.info("Purged expired news articles", extra={"deleted": deleted})


__all__ = ["NewsFetcher"]
