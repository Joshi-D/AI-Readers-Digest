"""LLM-backed content scoring for shortlisted articles."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace
import time

from openai import APIConnectionError, APIError, APITimeoutError, RateLimitError
from pydantic import ValidationError

from config.settings import CONTENT_BATCH_SIZE, MAX_RETRIES, MODEL_NAME
from models.article import Article
from models.content_scores import BatchContentScoreResponse
from ranking.scoring import compute_content_score
from utils.llm_client import get_openai_client
from utils.logger import get_logger


logger = get_logger(__name__)

SYSTEM_PROMPT = """You score full article content for an AI news digest.
Evaluate actual informational value, not title relevance.

Score:
- technical_depth: concrete implementation detail, engineering substance, or research depth
- business_impact: likely effect on companies, markets, products, or adoption
- novelty: new information compared with routine AI/technology coverage
- signal_to_noise: dense useful information versus fluff, hype, repetition, or ads
- actionability: usefulness for AI/technology professionals deciding what to learn, build, or monitor

Penalize shallow reporting, recycled announcements, hype articles, and low-detail summaries.
Return JSON only matching the requested schema. Scores must be integers from 1 to 10.
Be deterministic and concise. Do not include markdown or extra commentary."""


def _batch_articles(articles: list[Article], batch_size: int) -> Iterable[list[Article]]:
    for index in range(0, len(articles), batch_size):
        yield articles[index : index + batch_size]


def _format_articles_for_prompt(articles: list[Article]) -> str:
    formatted_articles: list[str] = []
    for article in articles:
        formatted_articles.append(
            "\n".join(
                [
                    f"article_id: {article.id}",
                    f"title: {article.title}",
                    f"source: {article.source}",
                    f"published_at: {article.published_at}",
                    "content:",
                    article.content or "",
                ]
            )
        )
    return "\n\n---\n\n".join(formatted_articles)


def _score_batch_once(articles: list[Article]) -> BatchContentScoreResponse:
    client = get_openai_client()
    prompt = (
        "Score these shortlisted articles using their cleaned content.\n\n"
        f"{_format_articles_for_prompt(articles)}"
    )

    started_at = time.perf_counter()
    response = client.beta.chat.completions.parse(
        model=MODEL_NAME,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format=BatchContentScoreResponse,
    )
    latency_ms = (time.perf_counter() - started_at) * 1000

    usage = getattr(response, "usage", None)
    if usage:
        logger.info(
            "content scoring api latency_ms=%.0f prompt_tokens=%s completion_tokens=%s total_tokens=%s",
            latency_ms,
            getattr(usage, "prompt_tokens", None),
            getattr(usage, "completion_tokens", None),
            getattr(usage, "total_tokens", None),
        )
    else:
        logger.info("content scoring api latency_ms=%.0f token_usage=unavailable", latency_ms)

    parsed = response.choices[0].message.parsed
    if parsed is None:
        logger.error("content scoring invalid schema output: parsed response is empty")
        raise ValueError("OpenAI response did not parse into BatchContentScoreResponse")

    return parsed


def _validate_batch_response(
    articles: list[Article],
    response: BatchContentScoreResponse,
) -> None:
    expected_ids = {article.id for article in articles}
    returned_ids = [score.article_id for score in response.results]
    returned_id_set = set(returned_ids)
    duplicate_ids = sorted(
        article_id for article_id in returned_id_set if returned_ids.count(article_id) > 1
    )
    missing_ids = sorted(expected_ids - returned_id_set)
    unknown_ids = sorted(returned_id_set - expected_ids)

    if duplicate_ids or missing_ids or unknown_ids:
        logger.error(
            "content scoring invalid output duplicate_ids=%s missing_ids=%s unknown_ids=%s",
            duplicate_ids,
            missing_ids,
            unknown_ids,
        )
        raise ValueError("OpenAI response did not contain exactly one score per article")


def _score_batch_with_retries(articles: list[Article]) -> BatchContentScoreResponse:
    last_error: Exception | None = None
    retryable_errors = (
        APIConnectionError,
        APIError,
        APITimeoutError,
        RateLimitError,
        TimeoutError,
        ValueError,
        ValidationError,
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = _score_batch_once(articles)
            _validate_batch_response(articles, response)
            return response
        except retryable_errors as error:
            last_error = error
            logger.warning(
                "content scoring retry attempt=%s max_retries=%s error=%s",
                attempt,
                MAX_RETRIES,
                error,
            )
            if attempt == MAX_RETRIES:
                break
            time.sleep(2 ** (attempt - 1))
        except Exception as error:
            last_error = error
            logger.exception("content scoring failure")
            if attempt == MAX_RETRIES:
                break
            time.sleep(2 ** (attempt - 1))

    raise RuntimeError("content scoring failed after retries") from last_error


def _apply_scores(
    articles: list[Article],
    scores: BatchContentScoreResponse,
) -> list[Article]:
    articles_by_id = {article.id: article for article in articles}
    scored_articles: list[Article] = []

    for score in scores.results:
        article = articles_by_id.get(score.article_id)
        if article is None:
            logger.warning("content scoring returned unknown article_id=%s", score.article_id)
            continue

        final_score = compute_content_score(
            score.technical_depth,
            score.business_impact,
            score.novelty,
            score.signal_to_noise,
            score.actionability,
        )
        scored_articles.append(
            replace(
                article,
                technical_depth=float(score.technical_depth),
                business_impact=float(score.business_impact),
                content_novelty=float(score.novelty),
                signal_to_noise=float(score.signal_to_noise),
                actionability=float(score.actionability),
                content_score=final_score,
                content_reason=score.reason,
            )
        )

    return scored_articles


def score_article_content(articles: list[Article]) -> list[Article]:
    """Score cleaned article content and return final content-ranked articles."""

    articles_with_content = [article for article in articles if article.content]
    skipped = len(articles) - len(articles_with_content)
    if skipped:
        logger.warning("content scoring skipped articles_without_content=%s", skipped)
    if not articles_with_content:
        return []

    logger.info("Scoring content batches...")
    scored_articles: list[Article] = []
    for batch in _batch_articles(articles_with_content, CONTENT_BATCH_SIZE):
        logger.info("content scoring batch size=%s", len(batch))
        batch_scores = _score_batch_with_retries(batch)
        scored_articles.extend(_apply_scores(batch, batch_scores))

    return sorted(
        scored_articles,
        key=lambda article: article.content_score or 0,
        reverse=True,
    )
