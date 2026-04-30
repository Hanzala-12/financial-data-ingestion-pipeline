"""Sentiment data loader for the API."""

from pathlib import Path
from typing import List

import pandas as pd

from src.market_direction.pipeline import DEFAULT_SENTIMENT_PATH, normalize_ticker


def load_recent_sentiment(
    ticker: str,
    hours: int = 24,
    sentiment_path: Path = DEFAULT_SENTIMENT_PATH,
) -> List[dict]:
    """Load sentiment records for the last N hours for a ticker."""
    ticker = normalize_ticker(ticker)
    sentiment_path = Path(sentiment_path)

    if not sentiment_path.exists():
        raise FileNotFoundError(f"Sentiment file not found: {sentiment_path}")

    df = pd.read_parquet(sentiment_path)
    if df.empty:
        return []

    df = df.copy()
    df["hour"] = pd.to_datetime(df["hour"], errors="coerce")
    df = df.dropna(subset=["hour"])
    df["ticker"] = df["ticker"].map(normalize_ticker)

    df = df[df["ticker"] == ticker]
    if df.empty:
        return []

    latest = df["hour"].max()
    cutoff = latest - pd.Timedelta(hours=hours)
    df = df[df["hour"] >= cutoff].sort_values("hour")

    records = df.to_dict(orient="records")
    for record in records:
        hour_value = record.get("hour")
        if hasattr(hour_value, "isoformat"):
            record["hour"] = hour_value.isoformat()
    return records
