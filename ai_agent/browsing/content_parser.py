"""Extract readable article text from HTML."""

from __future__ import annotations

from bs4 import BeautifulSoup


def extract_article_text(html: str) -> str:
    """Extract article-like text from an HTML document."""

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    article = soup.find("article") or soup.find("main") or soup.body or soup
    paragraphs = [
        paragraph.get_text(" ", strip=True)
        for paragraph in article.find_all("p")
        if paragraph.get_text(strip=True)
    ]

    return "\n\n".join(paragraphs)

