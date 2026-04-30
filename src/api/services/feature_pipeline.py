"""Feature preparation for inference."""

from pathlib import Path
import numpy as np

from src.market_direction.pipeline import (
    DEFAULT_PRICE_DIR,
    DEFAULT_SENTIMENT_PATH,
    FEATURE_COLUMNS,
    load_price_data,
    load_sentiment_data,
    normalize_ticker as _normalize_ticker,
    prepare_feature_frame,
)


def normalize_ticker(value: str) -> str:
    """Normalize ticker symbols for inference."""
    return _normalize_ticker(value)


def get_latest_features(
    ticker: str,
    window_size: int = 24,
    price_dir: Path = DEFAULT_PRICE_DIR,
    sentiment_path: Path = DEFAULT_SENTIMENT_PATH,
) -> np.ndarray:
    """Return the latest feature window for a ticker."""
    ticker = normalize_ticker(ticker)

    price_df = load_price_data(price_dir)
    sentiment_ts = load_sentiment_data(sentiment_path)
    feature_frame = prepare_feature_frame(
        price_df,
        sentiment_ts,
        missing_strategy="fill",
    )

    subset = (
        feature_frame[feature_frame["ticker"] == ticker]
        .sort_values("hour")
        .reset_index(drop=True)
    )

    if len(subset) < window_size:
        raise ValueError(
            f"Not enough data for {ticker}: need {window_size} rows, have {len(subset)}"
        )

    window = subset[FEATURE_COLUMNS].tail(window_size).to_numpy(dtype=np.float32)
    return np.expand_dims(window, axis=0)
