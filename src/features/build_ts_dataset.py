"""Build time-series datasets from price and sentiment data."""

from __future__ import annotations

from pathlib import Path
import argparse
import json

import numpy as np

from src.market_direction.pipeline import (
    DEFAULT_FALLBACK_CSV_PATH,
    DEFAULT_FALLBACK_SENTIMENT_PATH,
    DEFAULT_PRICE_DIR,
    DEFAULT_SENTIMENT_PATH,
    build_sliding_windows,
    load_price_data,
    load_sentiment_data,
    prepare_feature_frame,
)

DEFAULT_OUTPUT_DIR = Path("data/processed")
DEFAULT_FEATURE_FRAME_PATH = DEFAULT_OUTPUT_DIR / "market_feature_frame.parquet"
DEFAULT_SEQUENCE_PATH = DEFAULT_OUTPUT_DIR / "time_series_sequences.npz"
DEFAULT_METADATA_PATH = DEFAULT_OUTPUT_DIR / "time_series_dataset.json"


def build_time_series_dataset(
    price_dir: Path = DEFAULT_PRICE_DIR,
    sentiment_path: Path = DEFAULT_SENTIMENT_PATH,
    fallback_sentiment_path: Path = DEFAULT_FALLBACK_SENTIMENT_PATH,
    fallback_csv_path: Path = DEFAULT_FALLBACK_CSV_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    window_size: int = 24,
    missing_strategy: str = "fill",
    add_technical_indicators: bool = True,
) -> dict[str, Path]:
    """Create aligned market features and sliding windows for model training."""
    price_df = load_price_data(price_dir)
    sentiment_ts = load_sentiment_data(
        sentiment_path,
        fallback_path=fallback_sentiment_path,
        fallback_csv_path=fallback_csv_path,
    )

    feature_frame = prepare_feature_frame(
        price_df,
        sentiment_ts,
        missing_strategy=missing_strategy,
        add_technical_indicators=add_technical_indicators,
    )
    features, labels = build_sliding_windows(feature_frame, window_size=window_size)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    feature_frame_path = output_dir / DEFAULT_FEATURE_FRAME_PATH.name
    feature_frame.to_parquet(feature_frame_path, index=False)

    sequence_path = output_dir / DEFAULT_SEQUENCE_PATH.name
    np.savez_compressed(sequence_path, features=features, labels=labels)

    metadata = {
        "rows": int(len(feature_frame)),
        "windows": int(len(features)),
        "window_size": int(window_size),
        "feature_columns": list(feature_frame.columns),
    }
    metadata_path = output_dir / DEFAULT_METADATA_PATH.name
    metadata_path.write_text(json.dumps(metadata, indent=2))

    return {
        "feature_frame": feature_frame_path,
        "sequences": sequence_path,
        "metadata": metadata_path,
    }



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the time-series dataset")
    parser.add_argument("--price-dir", type=Path, default=DEFAULT_PRICE_DIR)
    parser.add_argument("--sentiment-path", type=Path, default=DEFAULT_SENTIMENT_PATH)
    parser.add_argument(
        "--fallback-sentiment-path",
        type=Path,
        default=DEFAULT_FALLBACK_SENTIMENT_PATH,
    )
    parser.add_argument(
        "--fallback-csv-path",
        type=Path,
        default=DEFAULT_FALLBACK_CSV_PATH,
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--window-size", type=int, default=24)
    parser.add_argument(
        "--missing-strategy",
        choices=["fill", "drop"],
        default="fill",
    )
    parser.add_argument("--no-technical-indicators", action="store_true")
    return parser.parse_args()



def main() -> None:
    args = parse_args()
    result = build_time_series_dataset(
        price_dir=args.price_dir,
        sentiment_path=args.sentiment_path,
        fallback_sentiment_path=args.fallback_sentiment_path,
        fallback_csv_path=args.fallback_csv_path,
        output_dir=args.output_dir,
        window_size=args.window_size,
        missing_strategy=args.missing_strategy,
        add_technical_indicators=not args.no_technical_indicators,
    )
    print(json.dumps({key: str(value) for key, value in result.items()}, indent=2))


if __name__ == "__main__":
    main()
