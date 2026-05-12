"""Sentiment processing pipeline for raw parquet files."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional
import logging

import pandas as pd

from .aggregator import aggregate_sentiment
from .config import SentimentConfig
from .finbert_model import classify_finbert_batch
from .utils import (
    RAW_DIR,
    PROCESSED_DIR,
    extract_ticker_from_text,
    normalize_ticker,
    save_parquet,
    setup_logging,
)
from .vader_model import classify_vader_batch

logger = logging.getLogger(__name__)


def infer_source(file_path: Path, df: pd.DataFrame) -> str:
    """Infer the data source from columns or file path."""
    if "source" in df.columns:
        source_values = df["source"].dropna().astype(str).str.lower().unique()
        if len(source_values) > 0:
            return source_values[0]

    columns = {col.lower() for col in df.columns}
    if "subreddit" in columns:
        return "reddit"
    if "cashtag" in columns:
        return "twitter"
    if "published_date" in columns or "link" in columns:
        return "reuters"

    path_str = str(file_path).lower()
    for key in ("reddit", "twitter", "reuters", "news"):
        if key in path_str:
            return "reuters" if key == "news" else key

    return "unknown"


def infer_source_from_path(file_path: Path) -> str:
    """Infer source based on the file path alone."""
    path_str = str(file_path).lower()
    if "reuters" in path_str or "news" in path_str:
        return "reuters"
    if "reddit" in path_str:
        return "reddit"
    if "twitter" in path_str:
        return "twitter"
    return "unknown"


def build_text_column(df: pd.DataFrame, source: str) -> pd.Series:
    """Construct the text column to classify based on source."""
    if source == "reddit":
        title = df.get("title", "").fillna("").astype(str)
        body = df.get("selftext", "").fillna("").astype(str)
        text = (title + " " + body).str.strip()
    elif source == "twitter":
        text = df.get("text", "").fillna("").astype(str)
    elif source == "reuters":
        text = df.get("title", "").fillna("").astype(str)
    else:
        if "text" in df.columns:
            text = df["text"].fillna("").astype(str)
        elif "title" in df.columns:
            text = df["title"].fillna("").astype(str)
        else:
            raise ValueError("No text column found for sentiment classification")

    return text


def resolve_timestamp(df: pd.DataFrame, source: str) -> pd.Series:
    """Resolve the timestamp column for a source into pandas datetime."""
    if "timestamp" in df.columns:
        timestamp = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    elif source == "reddit" and "created_utc" in df.columns:
        timestamp = pd.to_datetime(df["created_utc"], unit="s", utc=True, errors="coerce")
    elif source == "twitter" and "created_at" in df.columns:
        timestamp = pd.to_datetime(df["created_at"], utc=True, errors="coerce")
    elif source == "reuters" and "published_date" in df.columns:
        timestamp = pd.to_datetime(df["published_date"], utc=True, errors="coerce")
    elif "created_at" in df.columns:
        timestamp = pd.to_datetime(df["created_at"], utc=True, errors="coerce")
    elif "published_date" in df.columns:
        timestamp = pd.to_datetime(df["published_date"], utc=True, errors="coerce")
    else:
        timestamp = pd.to_datetime(pd.Series([None] * len(df)), utc=True, errors="coerce")

    return timestamp.dt.tz_convert(None)


def extract_ticker(df: pd.DataFrame, source: str, text_series: pd.Series) -> pd.Series:
    """Extract ticker symbols for grouping."""
    if "ticker" in df.columns:
        return df["ticker"].fillna("UNKNOWN").map(normalize_ticker)

    if "cashtag" in df.columns:
        return df["cashtag"].fillna("UNKNOWN").map(normalize_ticker)

    extracted = extract_ticker_from_text(text_series)
    if extracted.notna().any() and (extracted != "UNKNOWN").any():
        return extracted

    if "subreddit" in df.columns:
        return df["subreddit"].fillna("UNKNOWN").map(normalize_ticker)

    return pd.Series(["UNKNOWN"] * len(df), index=df.index)


def process_parquet(
    file_path: Path,
    finbert_pipeline=None,
    vader_analyzer=None,
    config: Optional[SentimentConfig] = None,
) -> pd.DataFrame:
    """Process a single raw parquet file and add sentiment labels."""
    config = config or SentimentConfig()
    df = pd.read_parquet(file_path)
    if df.empty:
        return pd.DataFrame(columns=["timestamp", "source", "ticker", "label", "score"])

    source = infer_source(Path(file_path), df)
    text_series = build_text_column(df, source)

    output = df.copy()
    output["source"] = source
    output["timestamp"] = resolve_timestamp(output, source)
    output["ticker"] = extract_ticker(output, source, text_series)

    text_list = text_series.fillna("").astype(str).tolist()

    if source in {"reuters", "news"}:
        labels, scores = classify_finbert_batch(
            text_list,
            classifier=finbert_pipeline,
            batch_size=config.finbert_batch_size,
        )
    else:
        labels, scores = classify_vader_batch(
            text_list,
            analyzer=vader_analyzer,
            pos_threshold=config.vader_pos_threshold,
            neg_threshold=config.vader_neg_threshold,
        )

    output["label"] = labels
    output["score"] = scores

    output = output.dropna(subset=["timestamp"])

    return output[["timestamp", "source", "ticker", "label", "score"]]


def process_raw_directory(
    raw_dir: Path = RAW_DIR,
    finbert_pipeline=None,
    vader_analyzer=None,
    config: Optional[SentimentConfig] = None,
) -> pd.DataFrame:
    """Process all raw parquet files under the raw data directory."""
    config = config or SentimentConfig()
    setup_logging(__name__, config.log_level)

    raw_dir = Path(raw_dir)
    file_paths = sorted(raw_dir.rglob("*.parquet"))

    if not file_paths:
        logger.warning("No parquet files found under %s", raw_dir)
        return pd.DataFrame(columns=["timestamp", "source", "ticker", "label", "score"])

    finbert_paths = []
    other_paths = []
    for file_path in file_paths:
        if infer_source_from_path(file_path) in {"reuters", "news"}:
            finbert_paths.append(file_path)
        else:
            other_paths.append(file_path)

    frames = []
    max_workers = config.max_workers if config.max_workers and config.max_workers > 1 else None

    if other_paths and max_workers:
        logger.info("Processing %d files with %d workers", len(other_paths), max_workers)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(
                    process_parquet,
                    file_path,
                    finbert_pipeline=finbert_pipeline,
                    vader_analyzer=vader_analyzer,
                    config=config,
                ): file_path
                for file_path in other_paths
            }

            for future in as_completed(future_map):
                file_path = future_map[future]
                try:
                    frame = future.result()
                except Exception as exc:
                    logger.warning("Skipping %s due to error: %s", file_path, exc)
                    continue

                if not frame.empty:
                    frames.append(frame)
    else:
        for file_path in other_paths:
            try:
                frame = process_parquet(
                    file_path,
                    finbert_pipeline=finbert_pipeline,
                    vader_analyzer=vader_analyzer,
                    config=config,
                )
                if not frame.empty:
                    frames.append(frame)
            except Exception as exc:
                logger.warning("Skipping %s due to error: %s", file_path, exc)

    for file_path in finbert_paths:
        try:
            frame = process_parquet(
                file_path,
                finbert_pipeline=finbert_pipeline,
                vader_analyzer=vader_analyzer,
                config=config,
            )
            if not frame.empty:
                frames.append(frame)
        except Exception as exc:
            logger.warning("Skipping %s due to error: %s", file_path, exc)

    if not frames:
        return pd.DataFrame(columns=["timestamp", "source", "ticker", "label", "score"])

    return pd.concat(frames, ignore_index=True)


def run_sentiment_pipeline(
    raw_dir: Path = RAW_DIR,
    output_path: Path = PROCESSED_DIR / "sentiment_hourly.parquet",
    config: Optional[SentimentConfig] = None,
) -> pd.DataFrame:
    """Run the full sentiment pipeline and save the hourly output."""
    config = config or SentimentConfig()
    setup_logging(__name__, config.log_level)

    logger.info("Running sentiment pipeline on %s", raw_dir)
    combined = process_raw_directory(raw_dir=raw_dir, config=config)
    sentiment_ts = aggregate_sentiment(combined)

    save_parquet(sentiment_ts, Path(output_path))
    logger.info("Saved hourly sentiment data to %s", output_path)
    return sentiment_ts


if __name__ == "__main__":
    run_sentiment_pipeline()
