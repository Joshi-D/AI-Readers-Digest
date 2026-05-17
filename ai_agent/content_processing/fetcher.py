"""HTTP fetching for article content."""

from __future__ import annotations

import time

import requests

from config.settings import settings
from utils.logger import get_logger


logger = get_logger(__name__)

DEFAULT_TIMEOUT_SECONDS = settings.request_timeout_seconds
DEFAULT_MAX_RETRIES = 3


def fetch_article_html(
    url: str,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> str:
    """Fetch article HTML with retries and graceful failure handling."""

    if not url:
        logger.warning("fetch failed: missing url")
        return ""

    headers = {"User-Agent": settings.user_agent}
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=timeout_seconds)
            response.raise_for_status()
            return response.text
        except requests.RequestException as error:
            logger.warning(
                "fetch failure attempt=%s max_retries=%s url=%s error=%s",
                attempt,
                max_retries,
                url,
                error,
            )
            if attempt == max_retries:
                break
            time.sleep(2 ** (attempt - 1))

    logger.error("fetch failed url=%s", url)
    return ""
