"""Unit tests for the FinBERT sentiment layer."""

from src.sentiment.finbert_model import classify_finbert, classify_finbert_batch


class DummyPipeline:
    def __init__(self, label: str, score: float):
        self.label = label
        self.score = score

    def __call__(self, texts, truncation=True, batch_size=None):
        if isinstance(texts, list):
            return [{"label": self.label, "score": self.score} for _ in texts]
        return [{"label": self.label, "score": self.score}]


def test_classify_finbert_positive_signed_score():
    pipeline = DummyPipeline("positive", 0.9)
    label, score = classify_finbert("Strong earnings report", classifier=pipeline)
    assert label == "positive"
    assert score == 0.9


def test_classify_finbert_negative_signed_score():
    pipeline = DummyPipeline("negative", 0.7)
    label, score = classify_finbert("Profit warning issued", classifier=pipeline)
    assert label == "negative"
    assert score == -0.7


def test_classify_finbert_batch():
    pipeline = DummyPipeline("neutral", 0.55)
    labels, scores = classify_finbert_batch(
        ["Headline one", "Headline two"],
        classifier=pipeline,
        batch_size=1,
    )
    assert labels == ["neutral", "neutral"]
    assert scores == [0.0, 0.0]
