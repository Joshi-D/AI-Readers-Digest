"""Deterministic RSS candidate generation before semantic ranking.

This module performs broad, non-editorial filtering before the LLM title
ranker runs.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Iterable

from config.settings import PRE_LLM_PER_SOURCE_CAP


logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


Entry = dict[str, Any]


def _group_by_source(entries: Iterable[Entry]) -> dict[str, list[Entry]]:
    grouped: dict[str, list[Entry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.get("source", "Unknown source")].append(entry)
    return dict(grouped)


def _sort_entries(entries: Iterable[Entry]) -> list[Entry]:
    return sorted(
        entries,
        key=lambda entry: (
            entry.get("published") is not None,
            entry.get("published") or datetime.min.replace(tzinfo=timezone.utc),
        ),
        reverse=True,
    )


def filter_recent_entries(entries: Iterable[Entry], hours: int) -> list[Entry]:
    """Return entries published within the requested window.

    Entries without a published timestamp are retained because some feeds omit
    timestamps even when the item is current.
    """

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=hours)

    return [
        entry
        for entry in entries
        if entry.get("published") is None or entry.get("published") >= cutoff
    ]


def _cap_source_entries(
    grouped_entries: dict[str, list[Entry]],
    per_source_cap: int,
) -> list[Entry]:
    capped_entries: list[Entry] = []

    for source, source_entries in sorted(grouped_entries.items()):
        sorted_source_entries = _sort_entries(source_entries)
        capped_source_entries = sorted_source_entries[:per_source_cap]
        capped_entries.extend(capped_source_entries)

        if len(source_entries) > per_source_cap:
            logger.info(
                "Source %s capped from %s -> %s",
                source,
                len(source_entries),
                len(capped_source_entries),
            )

    return capped_entries


def filter_last_n_hours(entries: list[Entry], hours: int) -> list[Entry]:
    """Generate deterministic pre-LLM candidates from recent RSS entries.

    The goal is to preserve broad source coverage while giving the downstream
    LLM ranker enough candidates to make semantic relevance, novelty, and
    importance decisions. Deterministic per-source pre-capping prevents a noisy
    or high-volume source from dominating the candidate pool.

    A broader candidate pool improves LLM ranking quality by
    letting the ranker compare more titles across sources before later top-N
    and diversity selection happens.
    """

    logger.info("Total entries before filtering: %s", len(entries))

    recent_entries = filter_recent_entries(entries, hours)
    logger.info("Entries after %sh filter: %s", hours, len(recent_entries))

    grouped_entries = _group_by_source(recent_entries)
    capped_entries = _cap_source_entries(
        grouped_entries,
        per_source_cap=PRE_LLM_PER_SOURCE_CAP,
    )
    final_entries = _sort_entries(capped_entries)

    logger.info("Final pre-LLM candidate pool: %s", len(final_entries))
    return final_entries


def filter_recent(entries: list[Entry], hours: int) -> list[Entry]:
    """Compatibility wrapper for older pipeline imports."""

    return filter_last_n_hours(entries, hours)
