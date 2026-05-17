"""Content cleaning and safe truncation before LLM scoring."""

from __future__ import annotations

import re

from utils.logger import get_logger


logger = get_logger(__name__)

MAX_CONTENT_CHARS = 5000

NOISE_PATTERNS = [
    r"(?i)\baccept (all )?cookies\b.*",
    r"(?i)\bmanage cookies\b.*",
    r"(?i)\bsubscribe\b.*\b(newsletter|now|today|sign up)\b.*",
    r"(?i)\bsign up\b.*\bnewsletter\b.*",
    r"(?i)\bshare (this|on|article)\b.*",
    r"(?i)\bfollow us\b.*",
    r"(?i)\badvertisement\b.*",
    r"(?i)\bsponsored content\b.*",
    r"(?i)\bcontinue reading\b.*",
]

INLINE_NOISE_PATTERNS = [
    r"(?i)\baccept (all )?cookies\b",
    r"(?i)\bmanage cookies\b",
    r"(?i)\badvertisement\b",
    r"(?i)\bsponsored content\b",
    r"(?i)\bshare this article\b",
]


def _remove_noise_lines(text: str) -> str:
    cleaned_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if any(re.fullmatch(pattern, stripped) for pattern in NOISE_PATTERNS):
            continue
        cleaned_lines.append(stripped)
    return "\n".join(cleaned_lines)


def _normalize_whitespace(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _truncate_safely(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text

    truncated = text[:max_chars]
    sentence_boundary = max(
        truncated.rfind(". "),
        truncated.rfind("? "),
        truncated.rfind("! "),
        truncated.rfind("\n\n"),
    )
    if sentence_boundary >= int(max_chars * 0.6):
        truncated = truncated[: sentence_boundary + 1]

    logger.info(
        "article content truncated original_chars=%s final_chars=%s",
        len(text),
        len(truncated),
    )
    return truncated.strip()


def clean_article_content(
    text: str,
    max_chars: int = MAX_CONTENT_CHARS,
) -> str:
    """Remove common page noise, normalize whitespace, and truncate safely."""

    if not text:
        return ""

    cleaned = _remove_noise_lines(text)
    for pattern in INLINE_NOISE_PATTERNS:
        cleaned = re.sub(pattern, " ", cleaned)
    cleaned = _normalize_whitespace(cleaned)
    return _truncate_safely(cleaned, max_chars)
