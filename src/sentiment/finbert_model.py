"""FinBERT sentiment layer for financial news headlines."""

from functools import lru_cache
from typing import Iterable, List, Optional, Tuple

from transformers import pipeline

_LABEL_MAP = {
    "positive": "positive",
    "negative": "negative",
    "neutral": "neutral",
    "pos": "positive",
    "neg": "negative",
    "neu": "neutral",
    "label_0": "positive",
    "label_1": "negative",
    "label_2": "neutral",
}


@lru_cache(maxsize=1)
def get_finbert_pipeline():
    """Load the FinBERT pipeline (no fine-tuning)."""
    return pipeline("text-classification", model="ProsusAI/finbert")


def normalize_finbert_label(raw_label: str) -> str:
    """Normalize FinBERT label output to positive/negative/neutral."""
    if not raw_label:
        return "neutral"

    key = raw_label.strip().lower()
    return _LABEL_MAP.get(key, "neutral")


def signed_finbert_score(label: str, probability: float) -> float:
    """Map FinBERT probability into a signed score in [-1, 1]."""
    prob = max(min(float(probability), 1.0), 0.0)
    if label == "positive":
        return prob
    if label == "negative":
        return -prob
    return 0.0


def classify_finbert(
    text: str,
    classifier=None,
) -> Tuple[str, float]:
    """Classify text with FinBERT.

    Args:
        text: Input headline text.
        classifier: Optional HuggingFace pipeline for tests or reuse.

    Returns:
        Tuple of (label, signed_score).
    """
    if not text:
        return "neutral", 0.0

    classifier = classifier or get_finbert_pipeline()
    result = classifier(text, truncation=True)

    if isinstance(result, list):
        result = result[0] if result else {"label": "neutral", "score": 0.0}

    label = normalize_finbert_label(result.get("label", "neutral"))
    score = signed_finbert_score(label, result.get("score", 0.0))
    return label, score


def classify_finbert_batch(
    texts: Iterable[str],
    classifier=None,
    batch_size: Optional[int] = None,
) -> Tuple[List[str], List[float]]:
    """Classify a batch of headlines with FinBERT."""
    text_list = list(texts)
    if not text_list:
        return [], []

    classifier = classifier or get_finbert_pipeline()

    results: List[dict] = []
    effective_batch = batch_size if batch_size and batch_size > 0 else None

    if effective_batch and effective_batch < len(text_list):
        for chunk in _chunk_texts(text_list, effective_batch):
            chunk_results = _run_classifier(classifier, chunk, effective_batch)
            if isinstance(chunk_results, dict):
                chunk_results = [chunk_results]
            results.extend(chunk_results)
    else:
        results = _run_classifier(classifier, text_list, effective_batch)
        if isinstance(results, dict):
            results = [results]

    labels: List[str] = []
    scores: List[float] = []

    for result in results:
        label = normalize_finbert_label(result.get("label", "neutral"))
        score = signed_finbert_score(label, result.get("score", 0.0))
        labels.append(label)
        scores.append(score)

    return labels, scores


def _chunk_texts(text_list: List[str], batch_size: int) -> Iterable[List[str]]:
    for start in range(0, len(text_list), batch_size):
        yield text_list[start : start + batch_size]


def _run_classifier(classifier, texts: List[str], batch_size: Optional[int]):
    if batch_size:
        return classifier(texts, truncation=True, batch_size=batch_size)
    return classifier(texts, truncation=True)
