"""Command line entrypoint for title and content article ranking."""

from __future__ import annotations

from dataclasses import replace

from config.settings import TITLE_SHORTLIST_SIZE
from content_processing.cleaner import clean_article_content
from content_processing.extractor import extract_article_text
from content_processing.fetcher import fetch_article_html
from ingestion.rss_reader import fetch_rss_entries
from ingestion.time_filter import filter_last_n_hours
from models.article import Article
from orchestration.digest_delivery import send_selected_digest
from ranking.content_ranker import score_article_content
from ranking.title_ranker import score_articles
from utils.logger import get_logger


logger = get_logger(__name__)


def _entry_to_article(entry: dict, index: int) -> Article:
    published = entry.get("published")
    published_at = published.isoformat() if published else ""
    return Article(
        id=str(entry.get("id") or entry.get("url") or index),
        title=entry.get("title", "Untitled"),
        url=entry.get("url") or entry.get("link", ""),
        source=entry.get("source", "Unknown source"),
        published_at=published_at,
    )


def _attach_clean_content(article: Article) -> Article:
    html = fetch_article_html(article.url)
    if not html:
        return replace(article, content="")

    raw_text = extract_article_text(html, article.url)
    if not raw_text:
        logger.warning("Failed extraction for article %s", article.id)
        return replace(article, content="")

    return replace(article, content=clean_article_content(raw_text))


def _fetch_and_clean_content(articles: list[Article]) -> list[Article]:
    logger.info("Fetching content for %s shortlisted articles", len(articles))
    enriched_articles = [_attach_clean_content(article) for article in articles]
    successful_articles = [article for article in enriched_articles if article.content]
    logger.info(
        "Successfully extracted content from %s articles",
        len(successful_articles),
    )
    return successful_articles


def _print_content_results(articles: list[Article]) -> None:
    print("\n==================================================")
    print("CONTENT SCORING RESULTS")
    print("==================================================\n")

    for index, article in enumerate(articles, start=1):
        print(f"Rank #{index}")
        print(f"Content Score: {article.content_score:.1f}")
        print(f"Technical Depth: {article.technical_depth:.0f}")
        print(f"Business Impact: {article.business_impact:.0f}")
        print(f"Novelty: {article.content_novelty:.0f}")
        print(f"Signal/Noise: {article.signal_to_noise:.0f}")
        print(f"Actionability: {article.actionability:.0f}")
        print(f"Title: {article.title}")
        print(f"Reason: {article.content_reason}")
        print()


def main() -> None:
    """Run title scoring, fetch shortlisted content, and print final rankings."""

    entries = fetch_rss_entries()
    recent_entries = filter_last_n_hours(entries, 72)
    articles = [
        _entry_to_article(entry, index)
        for index, entry in enumerate(recent_entries, start=1)
    ]

    title_ranked_articles = score_articles(articles)
    shortlisted_articles = title_ranked_articles[:TITLE_SHORTLIST_SIZE]
    logger.info("Selected top %s title-scored articles", len(shortlisted_articles))
    content_ready_articles = _fetch_and_clean_content(shortlisted_articles)
    content_ranked_articles = score_article_content(content_ready_articles)

    _print_content_results(content_ranked_articles)
    send_selected_digest(content_ranked_articles)


if __name__ == "__main__":
    main()
