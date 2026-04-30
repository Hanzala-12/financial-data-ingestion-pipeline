"""Unit tests for sentiment aggregation."""

import pandas as pd

from src.sentiment.aggregator import aggregate_sentiment


def test_aggregate_sentiment_hourly():
    df = pd.DataFrame(
        {
            "timestamp": [
                "2024-01-01 10:05:00",
                "2024-01-01 10:30:00",
                "2024-01-01 11:00:00",
            ],
            "ticker": ["AAPL", "AAPL", "AAPL"],
            "label": ["positive", "negative", "neutral"],
            "score": [0.8, -0.6, 0.0],
            "source": ["twitter", "twitter", "twitter"],
        }
    )

    out = aggregate_sentiment(df)

    hour_10 = out[out["hour"] == pd.Timestamp("2024-01-01 10:00:00")].iloc[0]
    hour_11 = out[out["hour"] == pd.Timestamp("2024-01-01 11:00:00")].iloc[0]

    assert hour_10["pos_count"] == 1
    assert hour_10["neg_count"] == 1
    assert hour_10["text_count"] == 2
    assert abs(hour_10["net_sentiment"]) < 1e-6

    assert hour_11["pos_count"] == 0
    assert hour_11["neg_count"] == 0
    assert hour_11["text_count"] == 1
    assert hour_11["net_sentiment"] == 0.0

def test_aggregate_sentiment_shape_and_index():
    df = pd.DataFrame(
        {
            "timestamp": [
                "2023-05-10 14:15:00",
                "2023-05-10 14:45:00",
                "2023-05-10 15:05:00",
            ],
            "ticker": ["MSFT", "MSFT", "TSLA"],
            "label": ["positive", "positive", "negative"],
            "score": [0.6, 0.7, -0.8],
            "source": ["reddit", "news", "twitter"],
        }
    )
    out = aggregate_sentiment(df)
    
    # 2 hours for MSFT + 1 hour for TSLA
    assert out.shape[0] == 2 
    
    expected_cols = [
        "hour",
        "ticker",
        "net_sentiment",
        "mean_score",
        "pos_count",
        "neg_count",
        "text_count",
    ]
    for col in expected_cols:
        assert col in out.columns

