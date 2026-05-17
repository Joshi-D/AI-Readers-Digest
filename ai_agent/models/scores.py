"""Structured LLM response schemas for article scoring."""

from pydantic import BaseModel, Field


class ArticleScore(BaseModel):
    article_id: str
    relevance_score: int = Field(ge=1, le=10)
    importance_score: int = Field(ge=1, le=10)
    novelty_score: int = Field(ge=1, le=10)
    reason: str


class BatchScoreResponse(BaseModel):
    results: list[ArticleScore]
