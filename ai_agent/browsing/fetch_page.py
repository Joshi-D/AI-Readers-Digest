"""Fetch and extract readable article content."""

from __future__ import annotations

import requests
from bs4 import BeautifulSoup


REQUEST_TIMEOUT_SECONDS = 8
MAX_CONTENT_CHARS = 4000
USER_AGENT = "AIReaderDigest/0.1"


def _clean_text(text: str) -> str:
    return " ".join(text.split())


def _extract_paragraphs(container) -> list[str]:
    paragraphs = []
    for paragraph in container.find_all("p"):
        text = _clean_text(paragraph.get_text(" ", strip=True))
        if text:
            paragraphs.append(text)
    return paragraphs


def fetch_article_content(url: str) -> str:
    """Fetch an article URL and return readable text content."""

    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        print(f"Failed to fetch article: {url} ({error})")
        return ""

    try:
        soup = BeautifulSoup(response.text, "html.parser")

        if "arxiv.org" in url:
            abstract = soup.find("blockquote", class_="abstract")
            if not abstract:
                return ""

            text = abstract.get_text().strip()
            if text.startswith("Abstract:"):
                text = text[len("Abstract:") :].strip()
            return text

        for tag in soup(["script", "style", "nav", "header", "footer", "noscript"]):
            tag.decompose()

        article = soup.find("article")
        if article:
            paragraphs = _extract_paragraphs(article)
        else:
            paragraphs = _extract_paragraphs(soup)

        content = "\n".join(paragraphs).strip()
        return content[:MAX_CONTENT_CHARS]
    except Exception as error:
        print(f"Failed to parse article: {url} ({error})")
        return ""


def fetch_multiple_articles(entries):
    """Return entries with fetched article content added."""

    enriched_entries = []

    for entry in entries:
        link = entry.get("link")
        if not link:
            print("Skipping article fetch: missing link")
            enriched_entries.append({**entry, "content": ""})
            continue

        print(f"Fetching article content: {link}")
        enriched_entries.append({**entry, "content": fetch_article_content(link)})

    return enriched_entries
