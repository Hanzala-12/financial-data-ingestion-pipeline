"""Sentiment analysis pipeline for financial text data."""

from .config import SentimentConfig
from .vader_model import classify_vader, classify_vader_batch, get_vader_analyzer
from .finbert_model import (
    classify_finbert,
    classify_finbert_batch,
    get_finbert_pipeline,
)
from .processor import process_parquet, process_raw_directory, run_sentiment_pipeline
from .aggregator import aggregate_sentiment

__all__ = [
    "classify_vader",
    "classify_vader_batch",
    "get_vader_analyzer",
    "SentimentConfig",
    "classify_finbert",
    "classify_finbert_batch",
    "get_finbert_pipeline",
    "process_parquet",
    "process_raw_directory",
    "run_sentiment_pipeline",
    "aggregate_sentiment",
]
