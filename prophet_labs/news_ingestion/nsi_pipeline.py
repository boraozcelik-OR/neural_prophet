"""Offline NLP enrichment pipeline for News & Signals Intelligence."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence

try:
    from langdetect import detect
except ImportError:  # pragma: no cover - optional dependency
    detect = None

try:
    from textblob import TextBlob
except ImportError:  # pragma: no cover - optional dependency
    TextBlob = None

import yaml

from prophet_labs.utils.logging import get_logger

LOGGER = get_logger(__name__)


@dataclass
class SentimentScores:
    polarity: float
    subjectivity: float


@dataclass
class EnrichedArticle:
    news_id: str
    source_id: str
    source_type: str
    feed_url: str
    title: str
    summary: str
    content: str
    language: str
    link: str
    published_at: Optional[str]
    tags_raw: List[str]
    metadata: Dict
    topics: List[str]
    entities: List[str]
    sentiment: SentimentScores
    risk_score: float
    political_domains: List[str]


class NsiPipeline:
    """Local NLP pipeline for topic detection, sentiment, and risk scoring."""

    def __init__(self, config_path: str) -> None:
        self.config = self._load_config(config_path)
        self.languages = self.config.get("languages", ["en"])
        self.sentiment_cfg = self.config.get("sentiment", {})
        self.risk_cfg = self.config.get("risk", {})

    @staticmethod
    def _load_config(path: str) -> Dict:
        with open(path, "r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

    def enrich(self, entry: Dict) -> Optional[EnrichedArticle]:
        content = entry.get("content") or entry.get("summary") or ""
        content = str(content)[: self.config.get("max_content_chars", 8000)]

        language = self._detect_language(content)
        if language and language not in self.languages:
            return None

        sentiment = self._sentiment(content)
        topics, political_domains = self._topics(content)
        entities = self._entities(content)
        risk = self._risk_score(sentiment.polarity, topics, political_domains, entry.get("source_type"))

        return EnrichedArticle(
            news_id=entry["news_id"],
            source_id=entry["source_id"],
            source_type=entry["source_type"],
            feed_url=entry.get("feed_url", ""),
            title=entry.get("title", ""),
            summary=entry.get("summary", ""),
            content=content,
            language=language or "unknown",
            link=entry.get("link", ""),
            published_at=entry.get("published_at"),
            tags_raw=entry.get("tags", []),
            metadata={"jurisdiction": entry.get("jurisdiction"), "category": entry.get("category")},
            topics=topics,
            entities=entities,
            sentiment=sentiment,
            risk_score=risk,
            political_domains=political_domains,
        )

    def _detect_language(self, text: str) -> Optional[str]:
        if detect is None:
            return self.languages[0] if self.languages else "en"
        try:
            return detect(text) if text else None
        except Exception:  # pragma: no cover - detection failures are non-fatal
            return None

    def _sentiment(self, text: str) -> SentimentScores:
        polarity = 0.0
        subjectivity = 0.0
        if TextBlob is not None and text:
            blob = TextBlob(text)
            polarity = float(blob.sentiment.polarity)
            subjectivity = float(blob.sentiment.subjectivity)
        polarity = self._keyword_adjustment(text, polarity)
        return SentimentScores(polarity=polarity, subjectivity=subjectivity)

    def _keyword_adjustment(self, text: str, polarity: float) -> float:
        neg_kw = self.sentiment_cfg.get("negative_keywords", [])
        pos_kw = self.sentiment_cfg.get("positive_keywords", [])
        weight_neg = float(self.sentiment_cfg.get("weight_negative", 1.0))
        weight_pos = float(self.sentiment_cfg.get("weight_positive", 1.0))
        text_lower = text.lower()
        for kw in neg_kw:
            if kw.lower() in text_lower:
                polarity -= 0.05 * weight_neg
        for kw in pos_kw:
            if kw.lower() in text_lower:
                polarity += 0.05 * weight_pos
        neutral_window = float(self.sentiment_cfg.get("neutral_window", 0.05))
        return max(-1.0, min(1.0, polarity if abs(polarity) > neutral_window else 0.0))

    def _topics(self, text: str) -> tuple[List[str], List[str]]:
        topics: List[str] = []
        domains: List[str] = []
        risk_domains = self.risk_cfg.get("domains", {})
        text_lower = text.lower()
        for domain, cfg in risk_domains.items():
            for kw in cfg.get("keywords", []):
                if kw.lower() in text_lower:
                    domains.append(domain)
                    topics.append(domain.replace("_", " "))
                    break
        if not domains:
            topics.append("general")
        return sorted(set(topics)), sorted(set(domains))

    def _entities(self, text: str) -> List[str]:
        candidates: Iterable[str] = re.findall(r"\b[A-Z][a-zA-Z]{2,}\b", text)
        return sorted(set(candidates))[:25]

    def _risk_score(self, polarity: float, topics: Sequence[str], domains: Sequence[str], source_type: Optional[str]) -> float:
        base = float(self.risk_cfg.get("base_weight", 0.5))
        topic_weight = float(self.risk_cfg.get("topic_weight", 0.3)) * len(topics)
        sentiment_weight = float(self.risk_cfg.get("sentiment_weight", 0.4)) * abs(polarity)
        count_weight = float(self.risk_cfg.get("count_weight", 0.2)) * len(domains)
        source_multiplier = 1.1 if source_type == "darkweb_osint" else 1.0
        score = base + topic_weight + sentiment_weight + count_weight
        return float(1 / (1 + math.exp(-score))) * source_multiplier
