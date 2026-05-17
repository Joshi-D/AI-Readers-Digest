"""OpenAI client factory."""

from functools import lru_cache

from openai import OpenAI

from config.settings import OPENAI_API_KEY


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    """Create a cached OpenAI SDK client."""

    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    return OpenAI(api_key=OPENAI_API_KEY)
