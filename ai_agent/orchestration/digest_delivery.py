"""Orchestrate final selection, summarization, formatting, and email delivery."""

from __future__ import annotations

from datetime import datetime
from dataclasses import asdict

from delivery.email_sender import send_email
from delivery.email_template import build_email_html
from models.article import Article
from processing.digest_builder import generate_editorial_insights, group_by_category
from processing.summarizer import FALLBACK_RESPONSE, summarize_article
from selection.top_articles import select_top_articles
from utils.logger import get_logger


logger = get_logger(__name__)


def _article_to_summarizer_payload(article: Article) -> dict:
    payload = asdict(article)
    payload["link"] = article.url
    payload["published"] = article.published_at
    return payload


def _summarize_selected_articles(articles: list[Article]) -> list[dict]:
    summarized_articles: list[dict] = []

    for index, article in enumerate(articles, start=1):
        logger.info(
            "summarization progress current=%s total=%s article_id=%s",
            index,
            len(articles),
            article.id,
        )
        payload = _article_to_summarizer_payload(article)

        try:
            summary = summarize_article(payload)
        except Exception as error:
            logger.exception(
                "summarizer failure article_id=%s title=%s error=%s",
                article.id,
                article.title,
                error,
            )
            continue

        if summary.get("summary") == FALLBACK_RESPONSE["summary"]:
            logger.warning("summary skipped article_id=%s reason=fallback_summary", article.id)
            continue

        summarized_articles.append({**payload, **summary})

    logger.info("summarization completed successful_articles=%s", len(summarized_articles))
    return summarized_articles


def send_selected_digest(scored_articles: list[Article]) -> bool:
    """Select top scored articles, summarize them, and send the email digest."""

    selected_articles = select_top_articles(scored_articles)
    if not selected_articles:
        logger.warning("email skipped reason=no_selected_articles")
        return False

    summarized_articles = _summarize_selected_articles(selected_articles)
    if not summarized_articles:
        logger.warning("email skipped reason=no_successful_summaries")
        return False

    grouped_articles = group_by_category(summarized_articles)
    editorial = generate_editorial_insights(summarized_articles)
    html = build_email_html(grouped_articles, editorial)

    subject = f"AI Reader's Digest | {datetime.now().strftime('%B %-d, %Y')}"
    logger.info("email sending started article_count=%s", len(summarized_articles))
    sent = send_email(subject, html)
    if sent:
        logger.info("email sending succeeded article_count=%s", len(summarized_articles))
    else:
        logger.warning("email sending failed article_count=%s", len(summarized_articles))
    return sent
