"""News & Signals Intelligence ingestion package.

This package provides configuration-driven connectors for RSS/Atom and JSON
feeds, enrichment via an offline NLP pipeline, and persistence of normalized
news articles that can later be aggregated into time series metrics.
"""

__all__ = [
    "rss_client",
    "fetcher",
    "nsi_pipeline",
]
