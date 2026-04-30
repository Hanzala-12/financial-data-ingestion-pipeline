"""Unit tests for sentiment utilities."""

import pandas as pd

from src.sentiment.utils import extract_ticker_from_text, normalize_ticker


def test_normalize_ticker_strips_dollar():
    assert normalize_ticker("$aapl") == "AAPL"


def test_extract_ticker_from_text():
    texts = pd.Series(["$TSLA jumps", "No ticker here"])
    tickers = extract_ticker_from_text(texts)
    assert tickers.iloc[0] == "TSLA"
    assert tickers.iloc[1] == "UNKNOWN"
