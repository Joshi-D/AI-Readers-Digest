"""Final deterministic article selection before summarization."""

from __future__ import annotations

from collections.abc import Iterable

from config.settings import FINAL_ARTICLE_COUNT
from models.article import Article
from utils.logger import get_logger


logger = get_logger(__name__)


def _article_key(article: Article) -> str:
    return article.url or article.id


def _is_valid_article(article: Article) -> bool:
    required_fields = {
        "id": article.id,
        "title": article.title,
        "url": article.url,
        "source": article.source,
        "content_score": article.content_score,
        "content": article.content,
    }
    missing_fields = [
        field_name
        for field_name, value in required_fields.items()
        if value is None or value == ""
    ]
    if missing_fields:
        logger.warning(
            "article skipped article_id=%s missing_fields=%s",
            article.id,
            missing_fields,
        )
        return False
    return True


def select_top_articles(
    articles: Iterable[Article],
    limit: int = FINAL_ARTICLE_COUNT,
) -> list[Article]:
    """Select the highest content-scored unique articles for summarization.

    This is intentionally deterministic: it only validates, de-duplicates, sorts
    by already-computed content score, and slices the top articles. Editorial
    scoring remains upstream in the LLM rankers.
    """

    article_list = list(articles)
    logger.info("selection received total_articles=%s", len(article_list))

    unique_articles: dict[str, Article] = {}
    for article in article_list:
        if not _is_valid_article(article):
            continue

        key = _article_key(article)
        existing = unique_articles.get(key)
        if existing is None or (article.content_score or 0) > (existing.content_score or 0):
            unique_articles[key] = article
        else:
            logger.info("duplicate article skipped article_id=%s url=%s", article.id, article.url)

    ranked_articles = sorted(
        unique_articles.values(),
        key=lambda article: article.content_score or 0,
        reverse=True,
    )
    selected_articles = ranked_articles[:limit]

    logger.info(
        "selection selected_articles=%s requested_limit=%s",
        len(selected_articles),
        limit,
    )
    return selected_articles
