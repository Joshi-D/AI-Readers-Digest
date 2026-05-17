"""LLM-backed title relevance scoring for RSS articles."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace
import time

from openai import APIConnectionError, APIError, APITimeoutError, RateLimitError
from pydantic import ValidationError

from config.settings import BATCH_SIZE, MAX_RETRIES, MODEL_NAME
from models.article import Article
from models.scores import BatchScoreResponse
from ranking.scoring import compute_final_score
from utils.llm_client import get_openai_client
from utils.logger import get_logger


logger = get_logger(__name__)

SYSTEM_PROMPT = """You score RSS article titles for an AI news digest.
Evaluate each title for:
- relevance to AI/technology professionals
- importance of the news
- novelty compared with typical daily AI and technology news

Return JSON only matching the requested schema. Scores must be integers from 1 to 10.
Be deterministic and concise. Do not include markdown or extra commentary."""


def _batch_articles(articles: list[Article], batch_size: int) -> Iterable[list[Article]]:
    for index in range(0, len(articles), batch_size):
        yield articles[index : index + batch_size]


def _format_articles_for_prompt(articles: list[Article]) -> str:
    lines = []
    for article in articles:
        lines.append(
            "\n".join(
                [
                    f"article_id: {article.id}",
                    f"title: {article.title}",
                    f"source: {article.source}",
                    f"published_at: {article.published_at}",
                ]
            )
        )
    return "\n\n".join(lines)


def _score_batch_once(articles: list[Article]) -> BatchScoreResponse:
    client = get_openai_client()
    prompt = (
        "Score these article titles for inclusion in an AI/technology "
        "professional news digest.\n\n"
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
        response_format=BatchScoreResponse,
    )
    latency_ms = (time.perf_counter() - started_at) * 1000

    usage = getattr(response, "usage", None)
    if usage:
        logger.info(
            "title scoring api latency_ms=%.0f prompt_tokens=%s completion_tokens=%s total_tokens=%s",
            latency_ms,
            getattr(usage, "prompt_tokens", None),
            getattr(usage, "completion_tokens", None),
            getattr(usage, "total_tokens", None),
        )
    else:
        logger.info("title scoring api latency_ms=%.0f token_usage=unavailable", latency_ms)

    parsed = response.choices[0].message.parsed
    if parsed is None:
        logger.error("title scoring invalid schema output: parsed response is empty")
        raise ValueError("OpenAI response did not parse into BatchScoreResponse")

    return parsed


def _score_batch_with_retries(articles: list[Article]) -> BatchScoreResponse:
    last_error: Exception | None = None
    retryable_errors = (
        APIConnectionError,
        APIError,
        APITimeoutError,
        RateLimitError,
        TimeoutError,
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = _score_batch_once(articles)
            _validate_batch_response(articles, response)
            return response
        except ValidationError as error:
            logger.exception("title scoring invalid schema output")
            raise ValueError("OpenAI response failed schema validation") from error
        except retryable_errors as error:
            last_error = error
            logger.warning(
                "title scoring api failure attempt=%s max_retries=%s error=%s",
                attempt,
                MAX_RETRIES,
                error,
            )
            if attempt == MAX_RETRIES:
                break
            time.sleep(2 ** (attempt - 1))
        except Exception as error:
            last_error = error
            logger.exception("title scoring failure")
            if attempt == MAX_RETRIES:
                break
            time.sleep(2 ** (attempt - 1))

    raise RuntimeError("title scoring failed after retries") from last_error


def _validate_batch_response(
    articles: list[Article],
    response: BatchScoreResponse,
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
            "title scoring invalid output duplicate_ids=%s missing_ids=%s unknown_ids=%s",
            duplicate_ids,
            missing_ids,
            unknown_ids,
        )
        raise ValueError("OpenAI response did not contain exactly one score per article")


def _apply_scores(articles: list[Article], scores: BatchScoreResponse) -> list[Article]:
    articles_by_id = {article.id: article for article in articles}
    scored_articles: list[Article] = []

    for score in scores.results:
        article = articles_by_id.get(score.article_id)
        if article is None:
            logger.warning("title scoring returned unknown article_id=%s", score.article_id)
            continue

        final_score = compute_final_score(
            score.relevance_score,
            score.importance_score,
            score.novelty_score,
        )
        scored_articles.append(
            replace(
                article,
                relevance_score=float(score.relevance_score),
                importance_score=float(score.importance_score),
                novelty_score=float(score.novelty_score),
                final_score=final_score,
                relevance_reason=score.reason,
            )
        )

    scored_ids = {article.id for article in scored_articles}
    missing_ids = set(articles_by_id) - scored_ids
    if missing_ids:
        logger.warning("title scoring missing article_ids=%s", sorted(missing_ids))

    return scored_articles


def score_articles(articles: list[Article]) -> list[Article]:
    """Score articles by title in batches and return them sorted by final score."""

    if not articles:
        return []

    scored_articles: list[Article] = []
    for batch in _batch_articles(articles, BATCH_SIZE):
        logger.info("title scoring batch size=%s", len(batch))
        batch_scores = _score_batch_with_retries(batch)
        scored_articles.extend(_apply_scores(batch, batch_scores))

    return sorted(
        scored_articles,
        key=lambda article: article.final_score or 0,
        reverse=True,
    )
