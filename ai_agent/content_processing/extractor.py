"""Readable text extraction from article HTML."""

from __future__ import annotations

from bs4 import BeautifulSoup

from utils.logger import get_logger


logger = get_logger(__name__)

DROP_TAGS = [
    "script",
    "style",
    "noscript",
    "nav",
    "header",
    "footer",
    "aside",
    "form",
    "iframe",
    "svg",
]


def _normalize_text(text: str) -> str:
    return " ".join(text.split())


def _extract_paragraphs(container) -> list[str]:
    paragraphs: list[str] = []
    for paragraph in container.find_all(["p", "li"]):
        text = _normalize_text(paragraph.get_text(" ", strip=True))
        if len(text) >= 40:
            paragraphs.append(text)
    return paragraphs


def extract_article_text(html: str, url: str = "") -> str:
    """Extract readable article text from HTML."""

    if not html:
        logger.warning("extraction failed url=%s reason=empty_html", url)
        return ""

    try:
        soup = BeautifulSoup(html, "html.parser")

        if "arxiv.org" in url:
            abstract = soup.find("blockquote", class_="abstract")
            if abstract:
                text = abstract.get_text(" ", strip=True)
                return text.removeprefix("Abstract:").strip()

        for tag in soup(DROP_TAGS):
            tag.decompose()

        for selector in [
            "[role='navigation']",
            "[aria-label*='navigation' i]",
            ".newsletter",
            ".subscribe",
            ".subscription",
            ".social",
            ".share",
            ".advertisement",
            ".ad",
        ]:
            for node in soup.select(selector):
                node.decompose()

        container = (
            soup.find("article")
            or soup.find("main")
            or soup.find(attrs={"role": "main"})
            or soup.body
            or soup
        )
        paragraphs = _extract_paragraphs(container)
        text = "\n\n".join(paragraphs).strip()
        if not text:
            logger.warning("extraction failed url=%s reason=no_readable_text", url)
        return text
    except Exception as error:
        logger.warning("extraction failure url=%s error=%s", url, error)
        return ""
