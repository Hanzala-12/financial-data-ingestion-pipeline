"""Generate a fallback sentiment CSV using Yahoo Finance data."""

from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf


def main() -> None:
    output_path = Path("data/fallback_sentiment_aggregated.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ticker = "AAPL"
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    df = yf.download(
        ticker,
        start=start_date,
        end=end_date,
        interval="1h",
        auto_adjust=False,
        progress=False,
    )
    if df.empty:
        raise ValueError("No Yahoo Finance data returned for fallback dataset.")

    df = df.reset_index()
    time_col = "Datetime" if "Datetime" in df.columns else "Date"

    keep_cols = ["Open", "High", "Low", "Close", "Volume"]
    if "Adj Close" in df.columns:
        keep_cols.append("Adj Close")

    df = df[[time_col] + keep_cols]
    df = df.rename(
        columns={
            time_col: "timestamp",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
            "Adj Close": "adj_close",
        }
    )

    if "adj_close" not in df.columns:
        df["adj_close"] = df["close"]

    df["sentiment_avg"] = 0.0
    df["sentiment_label"] = "neutral"
    df["ticker"] = ticker

    df.to_csv(output_path, index=False)
    print(f"Fallback dataset created with {len(df)} rows at {output_path}")


if __name__ == "__main__":
    main()
