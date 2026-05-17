"""Fetch and parse RSS feed entries."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List

import feedparser

from config.sources import RSS_FEEDS


def extract_datetime(entry):
    """
    Extract datetime from RSS entry using feedparser fields.
    Returns timezone-aware UTC datetime or None.
    """

    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
    return None


def _parse_feed(feed: Dict, seen_links: set[str]) -> List[Dict]:
    """Parse entries from a single feed config."""

    source_name = feed.get("name", "Unknown Source")
    feed_url = feed.get("url")

    if not feed_url:
        print(f"Skipping {source_name}: missing feed URL")
        return []

    try:
        parsed_feed = feedparser.parse(feed_url)
    except Exception as error:
        print(f"Failed to fetch {source_name}: {error}")
        return []

    if parsed_feed.bozo:
        print(f"Warning while parsing {source_name}: {parsed_feed.bozo_exception}")

    print(f"{source_name} → {len(parsed_feed.entries)} entries fetched")

    entries: List[Dict] = []
    for entry in parsed_feed.entries:
        title = entry.get("title")
        link = entry.get("link")

        if not title or not link:
            print(f"Skipping entry from {source_name}: missing title or link")
            continue

        if link in seen_links:
            print(f"Skipping duplicate entry: {link}")
            continue

        normalized_source = "arXiv" if "arXiv" in source_name else source_name

        seen_links.add(link)
        entries.append(
            {
                "title": title.strip(),
                "link": link.strip(),
                "published": extract_datetime(entry),
                "source": normalized_source,
            }
        )

    return entries


def fetch_rss_entries() -> List[Dict]:
    """Fetch RSS entries from configured feeds."""

    all_entries: List[Dict] = []
    seen_links: set[str] = set()

    for feed in RSS_FEEDS:
        all_entries.extend(_parse_feed(feed, seen_links))

    source_counts = defaultdict(int)
    for entry in all_entries:
        source_counts[entry["source"]] += 1

    print("\nEntries per source:")
    for source, count in source_counts.items():
        print(f"{source}: {count}")

    return all_entries
