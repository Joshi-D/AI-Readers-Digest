"""Structured LLM response schemas for content scoring."""

from pydantic import BaseModel, Field


class ContentScore(BaseModel):
    article_id: str
    technical_depth: int = Field(ge=1, le=10)
    business_impact: int = Field(ge=1, le=10)
    novelty: int = Field(ge=1, le=10)
    signal_to_noise: int = Field(ge=1, le=10)
    actionability: int = Field(ge=1, le=10)
    reason: str


class BatchContentScoreResponse(BaseModel):
    results: list[ContentScore]
