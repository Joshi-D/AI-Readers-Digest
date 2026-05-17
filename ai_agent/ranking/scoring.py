"""Deterministic score calculations."""


def compute_final_score(
    relevance_score: int,
    importance_score: int,
    novelty_score: int,
) -> float:
    """Compute the weighted final score for an article."""

    return (
        relevance_score * 0.5
        + importance_score * 0.3
        + novelty_score * 0.2
    )


def compute_content_score(
    technical_depth: int,
    business_impact: int,
    novelty: int,
    signal_to_noise: int,
    actionability: int,
) -> float:
    """Compute the weighted final content score for an article."""

    return (
        technical_depth * 0.25
        + business_impact * 0.30
        + novelty * 0.20
        + signal_to_noise * 0.20
        + actionability * 0.05
    )
