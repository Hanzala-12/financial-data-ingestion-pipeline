"""Unit tests for the VADER sentiment layer."""

from src.sentiment.vader_model import classify_vader, classify_vader_batch


def test_classify_vader_positive():
    label, score = classify_vader("I love this stock")
    assert label == "positive"
    assert score > 0.05


def test_classify_vader_negative():
    label, score = classify_vader("This is terrible")
    assert label == "negative"
    assert score < -0.05


def test_classify_vader_empty_is_neutral():
    label, score = classify_vader("")
    assert label == "neutral"
    assert score == 0.0


def test_classify_vader_batch_returns_lists():
    labels, scores = classify_vader_batch(["good", "bad"])
    assert len(labels) == 2
    assert len(scores) == 2


def test_classify_vader_custom_thresholds():
    class DummyAnalyzer:
        def polarity_scores(self, text):
            return {"compound": 0.2}

    label, score = classify_vader(
        "Neutral with high threshold",
        analyzer=DummyAnalyzer(),
        pos_threshold=0.3,
        neg_threshold=-0.3,
    )
    assert label == "neutral"
    assert score == 0.2
