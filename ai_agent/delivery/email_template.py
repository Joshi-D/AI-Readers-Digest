"""HTML email rendering for AI Reader's Digest."""

from __future__ import annotations

from datetime import datetime
from html import escape


CATEGORY_ORDER = [
    "New tools and launches",
    "Practical use cases",
    "Industry news",
    "Enterprise adoption",
    "Opinion",
]


def _safe_text(value, fallback=""):
    if value is None:
        return fallback
    return escape(str(value))


def _format_date(value):
    if isinstance(value, datetime):
        return value.strftime("%b %-d, %Y")
    if value:
        return str(value)
    return "Unknown date"


def _render_article(article):
    title = _safe_text(article.get("title"), "Untitled")
    summary = _safe_text(article.get("summary"), "Summary unavailable")
    source = _safe_text(article.get("source"), "Unknown source")
    published = _safe_text(_format_date(article.get("published")))
    link = _safe_text(article.get("link"))

    read_link = ""
    if link:
        read_link = f'<a class="read-link" href="{link}">Read Article &rarr;</a>'

    return f"""
        <article class="article-card">
          <h3>{title}</h3>
          <div class="meta">{source} &middot; {published}</div>
          <p>{summary}</p>
          {read_link}
        </article>
    """


def _render_category_sections(grouped_articles):
    sections = []

    for category in CATEGORY_ORDER:
        articles = grouped_articles.get(category, [])
        if not articles:
            continue

        cards = "\n".join(_render_article(article) for article in articles)
        sections.append(
            f"""
            <section class="category-section">
              <h2>{_safe_text(category)}</h2>
              {cards}
            </section>
            """
        )

    return "\n".join(sections)


def _render_questions(questions):
    if not questions:
        return '<p class="muted">No follow-up questions available.</p>'

    items = "\n".join(f"<li>{_safe_text(question)}</li>" for question in questions)
    return f'<ol class="questions">{items}</ol>'


def build_email_html(grouped_articles, editorial):
    """Convert grouped digest data and editorial insight into HTML."""

    today = datetime.now().strftime("%B %-d, %Y")
    featured = editorial.get("featured_perspective", {})
    featured_title = _safe_text(featured.get("title"), "Unavailable")
    featured_reason = _safe_text(
        featured.get("reason"),
        "Editorial insight unavailable",
    )
    questions = editorial.get("follow_up_questions", [])

    category_sections = _render_category_sections(grouped_articles)
    question_section = _render_questions(questions)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Reader's Digest</title>
  <style>
    body {{
      margin: 0;
      padding: 0;
      background: #f4f6f8;
      color: #1f2933;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
      line-height: 1.55;
    }}

    .page {{
      width: 100%;
      padding: 32px 14px;
      box-sizing: border-box;
    }}

    .container {{
      max-width: 700px;
      margin: 0 auto;
    }}

    .header {{
      background: #ffffff;
      border-radius: 18px;
      padding: 34px 34px 30px;
      box-shadow: 0 14px 40px rgba(15, 23, 42, 0.08);
      border: 1px solid #e6eaf0;
    }}

    .header h1 {{
      margin: 0;
      color: #111827;
      font-size: 30px;
      line-height: 1.18;
      letter-spacing: 0;
    }}

    .subtitle {{
      margin: 8px 0 0;
      color: #52616f;
      font-size: 16px;
    }}

    .date {{
      margin-top: 18px;
      color: #7b8794;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}

    .category-section {{
      margin-top: 26px;
    }}

    .category-section h2 {{
      margin: 0 0 14px;
      color: #111827;
      font-size: 20px;
      line-height: 1.3;
    }}

    .article-card {{
      margin: 0 0 14px;
      padding: 22px 24px;
      background: #ffffff;
      border: 1px solid #e6eaf0;
      border-radius: 14px;
      box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
    }}

    .article-card h3 {{
      margin: 0;
      color: #111827;
      font-size: 18px;
      line-height: 1.35;
    }}

    .meta {{
      margin-top: 8px;
      color: #7b8794;
      font-size: 13px;
    }}

    .article-card p {{
      margin: 14px 0 0;
      color: #334e68;
      font-size: 15px;
    }}

    .read-link {{
      display: inline-block;
      margin-top: 16px;
      color: #2563eb;
      font-size: 14px;
      font-weight: 700;
      text-decoration: none;
    }}

    .featured {{
      margin-top: 28px;
      padding: 24px 26px;
      background: #f8fbff;
      border: 1px solid #d9e8ff;
      border-left: 5px solid #2563eb;
      border-radius: 14px;
      box-shadow: 0 10px 28px rgba(15, 23, 42, 0.05);
    }}

    .featured h2,
    .questions-section h2 {{
      margin: 0;
      color: #111827;
      font-size: 20px;
      line-height: 1.3;
    }}

    .featured h3 {{
      margin: 16px 0 0;
      color: #172033;
      font-size: 18px;
      line-height: 1.35;
    }}

    .featured p {{
      margin: 10px 0 0;
      color: #334e68;
      font-size: 15px;
    }}

    .questions-section {{
      margin-top: 24px;
      padding: 24px 26px;
      background: #ffffff;
      border: 1px solid #e6eaf0;
      border-radius: 14px;
      box-shadow: 0 10px 28px rgba(15, 23, 42, 0.05);
    }}

    .questions {{
      margin: 16px 0 0;
      padding-left: 22px;
      color: #334e68;
      font-size: 15px;
    }}

    .questions li {{
      margin: 0 0 10px;
      padding-left: 4px;
    }}

    .muted {{
      margin: 14px 0 0;
      color: #7b8794;
      font-size: 15px;
    }}

    .footer {{
      padding: 24px 10px 6px;
      color: #8a96a3;
      font-size: 13px;
      text-align: center;
    }}

    @media (max-width: 560px) {{
      .page {{
        padding: 18px 10px;
      }}

      .header,
      .article-card,
      .featured,
      .questions-section {{
        border-radius: 12px;
        padding: 20px;
      }}

      .header h1 {{
        font-size: 25px;
      }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <main class="container">
      <header class="header">
        <h1>📰 AI Reader's Digest</h1>
        <p class="subtitle">Your daily AI intelligence briefing</p>
        <div class="date">{_safe_text(today)}</div>
      </header>

      {category_sections}

      <section class="featured">
        <h2>🧠 One Perspective Worth Thinking About</h2>
        <h3>{featured_title}</h3>
        <p>{featured_reason}</p>
      </section>

      <section class="questions-section">
        <h2>🔍 Questions Worth Exploring</h2>
        {question_section}
      </section>

      <footer class="footer">
        Generated by AI Reader's Digest Agent
      </footer>
    </main>
  </div>
</body>
</html>
"""
