"""Build and persist the feature frame for market direction models."""

from pathlib import Path

from .pipeline import (
    DEFAULT_FALLBACK_SENTIMENT_PATH,
    DEFAULT_FALLBACK_CSV_PATH,
    DEFAULT_PRICE_DIR,
    DEFAULT_SENTIMENT_PATH,
    load_price_data,
    load_sentiment_data,
    prepare_feature_frame,
)

DEFAULT_FEATURE_PATH = DEFAULT_SENTIMENT_PATH.parent / "feature_frame.parquet"


def build_feature_frame(
    price_dir: Path = DEFAULT_PRICE_DIR,
    sentiment_path: Path = DEFAULT_SENTIMENT_PATH,
    fallback_path: Path = DEFAULT_FALLBACK_SENTIMENT_PATH,
    fallback_csv_path: Path = DEFAULT_FALLBACK_CSV_PATH,
    output_path: Path = DEFAULT_FEATURE_PATH,
    missing_strategy: str = "fill",
    add_technical_indicators: bool = False,
) -> Path:
    """Build the merged feature frame and save it to disk."""
    price_df = load_price_data(price_dir)
    sentiment_ts = load_sentiment_data(
        sentiment_path,
        fallback_path=fallback_path,
        fallback_csv_path=fallback_csv_path,
    )

    feature_frame = prepare_feature_frame(
        price_df,
        sentiment_ts,
        missing_strategy=missing_strategy,
        add_technical_indicators=add_technical_indicators,
    )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    feature_frame.to_parquet(output_path, index=False)
    return output_path


if __name__ == "__main__":
    path = build_feature_frame()
    print(f"Saved feature frame to {path}")
