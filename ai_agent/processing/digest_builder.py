"""Build grouped digest sections and editorial insights."""

from __future__ import annotations

import json
import os
import re
from collections import defaultdict

from dotenv import load_dotenv
from openai import OpenAI


FALLBACK_EDITORIAL = {
    "featured_perspective": {
        "title": "Unavailable",
        "reason": "Editorial insight unavailable",
    },
    "follow_up_questions": [],
}


load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


def group_by_category(articles):
    """Group summarized articles by category while preserving input order."""

    grouped = defaultdict(list)
    for article in articles:
        grouped[article.get("category", "Industry news")].append(article)

    return dict(grouped)


def load_digest_prompt():
    """Load the digest builder prompt template."""

    prompt_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "prompts",
        "digest_builder.txt",
    )
    with open(prompt_path, "r", encoding="utf-8") as file:
        return file.read()


def extract_json(text):
    """Extract a JSON object from an LLM response."""

    if not text:
        return None

    text = text.strip()
    text = text.replace("```json", "").replace("```", "")

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)

    return None


def generate_editorial_insights(articles):
    """Generate one featured perspective and follow-up questions."""

    article_payload = [
        {
            "title": article.get("title", "Untitled"),
            "category": article.get("category", "Industry news"),
            "summary": article.get("summary", "Summary unavailable"),
        }
        for article in articles
    ]

    try:
        template = load_digest_prompt()
        prompt = template.replace(
            "{articles}",
            json.dumps(article_payload, ensure_ascii=False, indent=2),
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
        )

        output = response.choices[0].message.content
        clean_json = extract_json(output)
        if not clean_json:
            raise ValueError("No JSON found in response")

        result = json.loads(clean_json)
        return {
            "featured_perspective": result.get(
                "featured_perspective",
                FALLBACK_EDITORIAL["featured_perspective"],
            ),
            "follow_up_questions": result.get("follow_up_questions", []),
        }
    except Exception as error:
        print(f"Editorial insight generation failed: {error}")
        return FALLBACK_EDITORIAL.copy()
