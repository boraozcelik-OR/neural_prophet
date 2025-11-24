"""RSS/Atom client utilities for News & Signals Intelligence ingestion."""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import feedparser
import requests

from prophet_labs.utils.logging import get_logger

LOGGER = get_logger(__name__)


@dataclass
class FeedState:
    """Track incremental fetch hints for a feed."""

    etag: Optional[str] = None
    modified: Optional[time.struct_time] = None


@dataclass
class FeedEntry:
    """Normalized feed entry returned by the RSS client."""

    source_id: str
    source_type: str
    feed_url: str
    title: str
    summary: str
    link: str
    published_at: Optional[str]
    tags: List[str]
    raw: Dict

    @property
    def news_id(self) -> str:
        base = f"{self.link}|{self.published_at or ''}|{self.title}".encode("utf-8", "ignore")
        return hashlib.sha256(base).hexdigest()


class RssClient:
    """Fetches and parses RSS/Atom feeds with conservative defaults."""

    def __init__(
        self,
        timeout: int = 10,
        max_content_bytes: int = 256_000,
        user_agent: str = "ProphetLabs-NSI/1.0 (+https://serica-capital.example)",
    ) -> None:
        self.timeout = timeout
        self.max_content_bytes = max_content_bytes
        self.user_agent = user_agent

    def fetch(self, feed_url: str, source_id: str, source_type: str, state: Optional[FeedState] = None) -> Tuple[List[FeedEntry], FeedState]:
        """Fetch and parse a feed, honoring cache headers when provided."""

        self._validate_url(feed_url)
        headers = {"User-Agent": self.user_agent}
        if state and state.etag:
            headers["If-None-Match"] = state.etag
        if state and state.modified:
            headers["If-Modified-Since"] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", state.modified)

        response = requests.get(feed_url, headers=headers, timeout=self.timeout, stream=True)
        if response.status_code == 304:
            return [], state or FeedState(etag=response.headers.get("ETag"), modified=None)
        response.raise_for_status()
        content = response.content[: self.max_content_bytes]
        parsed = feedparser.parse(content)

        entries: List[FeedEntry] = []
        for entry in parsed.entries:
            published = self._parse_published(entry)
            summary = entry.get("summary", "")
            title = entry.get("title", "")
            link = entry.get("link", "")
            tags = [t.get("term") for t in entry.get("tags", []) if isinstance(t, dict) and t.get("term")]
            entries.append(
                FeedEntry(
                    source_id=source_id,
                    source_type=source_type,
                    feed_url=feed_url,
                    title=title,
                    summary=summary,
                    link=link,
                    published_at=published,
                    tags=tags,
                    raw=entry,
                )
            )

        new_state = FeedState(etag=response.headers.get("ETag"), modified=parsed.get("modified_parsed"))
        return entries, new_state

    def _validate_url(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError(f"Unsupported feed scheme for {url}")
        if not parsed.netloc:
            raise ValueError(f"Invalid feed URL {url}")

    @staticmethod
    def _parse_published(entry: Dict) -> Optional[str]:
        for key in ("published", "updated", "created"):
            if key in entry:
                return entry.get(key)
        return None
