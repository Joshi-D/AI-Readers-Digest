"""Article model shared by ranking and downstream digest steps."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Article:
    id: str
    title: str
    url: str
    source: str
    published_at: str
    summary: Optional[str] = None
    content: Optional[str] = None

    relevance_score: Optional[float] = None
    importance_score: Optional[float] = None
    novelty_score: Optional[float] = None
    final_score: Optional[float] = None
    relevance_reason: Optional[str] = None

    technical_depth: Optional[float] = None
    business_impact: Optional[float] = None
    content_novelty: Optional[float] = None
    signal_to_noise: Optional[float] = None
    actionability: Optional[float] = None

    content_score: Optional[float] = None
    content_reason: Optional[str] = None
