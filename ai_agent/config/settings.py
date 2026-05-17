"""Application settings."""

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
PRE_LLM_PER_SOURCE_CAP = int(os.getenv("PRE_LLM_PER_SOURCE_CAP", "10"))
TITLE_SHORTLIST_SIZE = int(os.getenv("TITLE_SHORTLIST_SIZE", "20"))
CONTENT_BATCH_SIZE = int(os.getenv("CONTENT_BATCH_SIZE", "4"))
FINAL_ARTICLE_COUNT = int(os.getenv("FINAL_ARTICLE_COUNT", "7"))


@dataclass(frozen=True)
class Settings:
    """Runtime limits and defaults."""

    openai_api_key: str = OPENAI_API_KEY
    model_name: str = MODEL_NAME
    batch_size: int = BATCH_SIZE
    max_retries: int = MAX_RETRIES
    pre_llm_per_source_cap: int = PRE_LLM_PER_SOURCE_CAP
    title_shortlist_size: int = TITLE_SHORTLIST_SIZE
    content_batch_size: int = CONTENT_BATCH_SIZE
    final_article_count: int = FINAL_ARTICLE_COUNT
    time_window_hours: int = 72
    max_articles_per_feed: int = 10
    max_total_articles: int = 25
    request_timeout_seconds: int = 15
    user_agent: str = "AIReaderDigest/0.1"
    prompt_path: Path = BASE_DIR / "prompts" / "summarization.txt"


settings = Settings()
