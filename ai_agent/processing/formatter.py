"""Format digest output for email or API delivery."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def format_digest(articles: list[dict[str, Any]]) -> dict[str, Any]:
    """Return a structured digest payload."""

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "article_count": len(articles),
        "articles": [
            {
                "title": article.get("title"),
                "url": article.get("url"),
                "source": article.get("source"),
                "published_at": article.get("published_at").isoformat()
                if article.get("published_at")
                else None,
                "summary": article.get("digest_summary"),
            }
            for article in articles
        ],
    }

