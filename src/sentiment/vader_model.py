"""VADER sentiment layer for social media text."""

from functools import lru_cache
from typing import Iterable, List, Optional, Tuple

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

POS_THRESHOLD = 0.05
NEG_THRESHOLD = -0.05


@lru_cache(maxsize=1)
def get_vader_analyzer() -> SentimentIntensityAnalyzer:
    """Return a cached VADER analyzer instance."""
    return SentimentIntensityAnalyzer()


def classify_vader(
    text: str,
    analyzer: Optional[SentimentIntensityAnalyzer] = None,
    pos_threshold: float = POS_THRESHOLD,
    neg_threshold: float = NEG_THRESHOLD,
) -> Tuple[str, float]:
    """Classify text with VADER.

    Args:
        text: Input text to classify.
        analyzer: Optional analyzer instance for reuse in tests.

    Returns:
        Tuple of (label, compound_score).
    """
    if not text:
        return "neutral", 0.0

    analyzer = analyzer or get_vader_analyzer()
    compound = analyzer.polarity_scores(text).get("compound", 0.0)

    if compound > pos_threshold:
        label = "positive"
    elif compound < neg_threshold:
        label = "negative"
    else:
        label = "neutral"

    return label, float(compound)


def classify_vader_batch(
    texts: Iterable[str],
    analyzer: Optional[SentimentIntensityAnalyzer] = None,
    pos_threshold: float = POS_THRESHOLD,
    neg_threshold: float = NEG_THRESHOLD,
) -> Tuple[List[str], List[float]]:
    """Classify a batch of texts with VADER.

    Args:
        texts: Iterable of input strings.
        analyzer: Optional analyzer instance for reuse.

    Returns:
        Tuple of labels list and scores list.
    """
    analyzer = analyzer or get_vader_analyzer()

    labels: List[str] = []
    scores: List[float] = []

    for text in texts:
        label, score = classify_vader(
            text or "",
            analyzer=analyzer,
            pos_threshold=pos_threshold,
            neg_threshold=neg_threshold,
        )
        labels.append(label)
        scores.append(score)

    return labels, scores
