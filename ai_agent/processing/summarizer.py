"""LLM-backed article summarization."""

from __future__ import annotations

import json
import os
import re

from dotenv import load_dotenv
from openai import OpenAI


FALLBACK_RESPONSE = {
    "summary": "Summary unavailable",
    "category": "Industry news",
}


load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


def load_prompt_template():
    try:
        with open("prompts/summarization.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError as error:
        raise FileNotFoundError(
            "Prompt file missing: prompts/summarization.txt"
        ) from error


def extract_json(text):
    if not text:
        return None

    text = text.strip()
    text = text.replace("```json", "").replace("```", "")

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)

    return None


def summarize_article(article: dict) -> dict:
    """Summarize an article and assign one digest category."""

    template = load_prompt_template()
    prompt = template.format(
        title=article["title"],
        content=article.get("content", "")[:2000],
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        output = response.choices[0].message.content
        clean_json = extract_json(output)
        if not clean_json:
            raise ValueError("No JSON found in response")

        result = json.loads(clean_json)
        return {
            "summary": result.get("summary", FALLBACK_RESPONSE["summary"]),
            "category": result.get("category", FALLBACK_RESPONSE["category"]),
        }
    except Exception as error:
        print(f"Summarization failed: {article['title']} -> {error}")
        return FALLBACK_RESPONSE.copy()


def summarize_multiple(articles: list) -> list:
    """Summarize multiple articles and append summary fields to each item."""

    summarized_articles = []
    for article in articles:
        summary = summarize_article(article)
        summarized_articles.append({**article, **summary})
    return summarized_articles
