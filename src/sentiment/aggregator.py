"""Time-series aggregation for sentiment signals."""

import pandas as pd


def aggregate_sentiment(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate sentiment into hourly windows per ticker.

    Args:
        df: DataFrame with timestamp, ticker, label, and score columns.

    Returns:
        Hourly aggregated sentiment DataFrame.
    """
    if df.empty:
        return pd.DataFrame(
            columns=[
                "hour",
                "ticker",
                "net_sentiment",
                "mean_score",
                "pos_count",
                "neg_count",
                "text_count",
            ]
        )

    working = df.copy()
    working["timestamp"] = pd.to_datetime(working["timestamp"], errors="coerce")
    working = working.dropna(subset=["timestamp", "ticker", "label"])

    working["hour"] = working["timestamp"].dt.floor("H")

    sentiment_ts = (
        working.groupby(["hour", "ticker"], as_index=False)
        .agg(
            pos_count=("label", lambda x: (x == "positive").sum()),
            neg_count=("label", lambda x: (x == "negative").sum()),
            neu_count=("label", lambda x: (x == "neutral").sum()),
            mean_score=("score", "mean"),
            text_count=("label", "count"),
        )
    )

    sentiment_ts["net_sentiment"] = (
        sentiment_ts["pos_count"] - sentiment_ts["neg_count"]
    ) / (sentiment_ts["text_count"] + 1e-6)

    return sentiment_ts[
        [
            "hour",
            "ticker",
            "net_sentiment",
            "mean_score",
            "pos_count",
            "neg_count",
            "text_count",
        ]
    ]
