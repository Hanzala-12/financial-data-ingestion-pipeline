"""Unit tests for the sentiment processor."""

from datetime import datetime
from pathlib import Path

import pandas as pd

from src.sentiment.processor import process_parquet


class DummyAnalyzer:
    def __init__(self, compound: float):
        self.compound = compound

    def polarity_scores(self, text):
        return {"compound": self.compound}


class DummyPipeline:
    def __init__(self, label: str, score: float):
        self.label = label
        self.score = score

    def __call__(self, texts, truncation=True, batch_size=None):
        if isinstance(texts, list):
            return [{"label": self.label, "score": self.score} for _ in texts]
        return [{"label": self.label, "score": self.score}]


def test_process_parquet_reddit_extracts_ticker(tmp_path: Path):
    df = pd.DataFrame(
        {
            "title": ["$MSFT to the moon"],
            "selftext": [""],
            "created_utc": [1700000000],
            "subreddit": ["stocks"],
        }
    )
    file_path = tmp_path / "reddit.parquet"
    df.to_parquet(file_path, index=False)

    out = process_parquet(file_path, vader_analyzer=DummyAnalyzer(0.8))

    assert set(out.columns) == {"timestamp", "source", "ticker", "label", "score"}
    assert out.loc[0, "source"] == "reddit"
    assert out.loc[0, "ticker"] == "MSFT"
    assert out.loc[0, "label"] == "positive"


def test_process_parquet_reuters_uses_finbert(tmp_path: Path):
    df = pd.DataFrame(
        {
            "title": ["Markets fall on inflation data"],
            "published_date": ["2024-01-01T10:15:00Z"],
        }
    )
    file_path = tmp_path / "reuters.parquet"
    df.to_parquet(file_path, index=False)

    out = process_parquet(file_path, finbert_pipeline=DummyPipeline("negative", 0.6))

    assert out.loc[0, "source"] == "reuters"
    assert out.loc[0, "label"] == "negative"
    assert out.loc[0, "score"] == -0.6
    assert pd.api.types.is_datetime64_any_dtype(out["timestamp"])
