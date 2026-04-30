"""
Yahoo Finance data ingestion module.

This module retrieves OHLCV (Open, High, Low, Close, Volume) data from Yahoo Finance
for specified tickers and saves it to Parquet format with metadata columns.
"""

import os
from datetime import datetime
from typing import List
import pandas as pd
import yfinance as yf

from .utils import setup_logging, get_timestamp_filename, save_to_parquet


def ingest_yahoo_data(
    tickers: List[str] = ["AAPL", "TSLA", "SPY"],
    interval: str = "1h",
    period: str = "60d"
) -> None:
    """
    Ingest OHLCV data from Yahoo Finance for specified tickers.
    
    For each ticker, retrieves historical market data and saves it to a Parquet file
    with added metadata columns (ticker symbol and ingestion timestamp).
    
    Args:
        tickers: List of ticker symbols (default: ["AAPL", "TSLA", "SPY"])
        interval: Data interval (default: "1h")
        period: Lookback period (default: "60d")
    
    Raises:
        Exception: Logs error and continues if individual ticker fails
    """
    logger = setup_logging("yahoo_ingest")
    logger.info(f"Starting Yahoo Finance ingestion for tickers: {tickers}")
    
    for ticker in tickers:
        try:
            logger.info(f"Fetching data for {ticker}")
            
            # Retrieve OHLCV data from Yahoo Finance
            ticker_obj = yf.Ticker(ticker)
            df = ticker_obj.history(period=period, interval=interval)
            
            # Check if data was retrieved
            if df.empty:
                logger.warning(f"No data retrieved for {ticker}")
                continue
            
            # Add metadata columns
            df['ticker'] = ticker
            df['ingested_at'] = datetime.now().isoformat()
            
            # Generate output path
            filename = get_timestamp_filename("yahoo", ticker)
            output_path = os.path.join("data", "raw", "yahoo", filename)
            
            # Save to Parquet
            save_to_parquet(df, output_path)
            
            logger.info(f"Completed ingestion for {ticker}: {len(df)} rows")
            
        except Exception as e:
            logger.error(f"Failed to ingest data for {ticker}: {e}", exc_info=True)
            continue


if __name__ == "__main__":
    ingest_yahoo_data()
