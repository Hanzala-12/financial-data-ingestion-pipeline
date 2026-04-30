"""Configuration for the sentiment pipeline."""

from dataclasses import dataclass
import os
from typing import Optional


@dataclass(frozen=True)
class SentimentConfig:
    """Runtime configuration for sentiment processing."""

    vader_pos_threshold: float = 0.05
    vader_neg_threshold: float = -0.05
    finbert_batch_size: int = 32
    max_workers: Optional[int] = None
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "SentimentConfig":
        """Build a config from environment variables."""
        defaults = cls()

        return cls(
            vader_pos_threshold=_get_float(
                "SENTIMENT_VADER_POS_THRESHOLD", defaults.vader_pos_threshold
            ),
            vader_neg_threshold=_get_float(
                "SENTIMENT_VADER_NEG_THRESHOLD", defaults.vader_neg_threshold
            ),
            finbert_batch_size=_get_int(
                "SENTIMENT_FINBERT_BATCH_SIZE", defaults.finbert_batch_size
            ),
            max_workers=_get_int("SENTIMENT_MAX_WORKERS", defaults.max_workers),
            log_level=_get_str("SENTIMENT_LOG_LEVEL", defaults.log_level),
        )


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _get_int(name: str, default: Optional[int]) -> Optional[int]:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_str(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value
