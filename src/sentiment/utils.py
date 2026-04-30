"""Utilities for the sentiment pipeline."""

from pathlib import Path
import logging
import re
from typing import Optional

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

_CASHTAG_PATTERN = re.compile(r"\$([A-Za-z]{1,6})")


def setup_logging(name: str, level: str = "INFO") -> logging.Logger:
    """Configure and return a logger with a standard format."""
    logger = logging.getLogger(name)
    numeric_level = getattr(logging, str(level).upper(), logging.INFO)
    logger.setLevel(numeric_level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    for handler in logger.handlers:
        handler.setLevel(numeric_level)

    return logger


def ensure_directory(path: Path) -> None:
    """Create a directory if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)


def normalize_ticker(value: Optional[str]) -> str:
    """Normalize ticker strings to uppercase without a leading $ sign."""
    if value is None:
        return "UNKNOWN"

    ticker = str(value).strip().upper()
    if ticker.startswith("$"):
        ticker = ticker[1:]

    return ticker or "UNKNOWN"


def extract_ticker_from_text(texts: pd.Series) -> pd.Series:
    """Extract the first cashtag-style ticker from a text series."""
    extracted = texts.str.extract(_CASHTAG_PATTERN, expand=False)
    return extracted.fillna("UNKNOWN").map(normalize_ticker)


def save_parquet(df: pd.DataFrame, path: Path) -> None:
    """Save a DataFrame to Parquet with Snappy compression."""
    ensure_directory(path.parent)
    df.to_parquet(path, engine="pyarrow", compression="snappy", index=False)
