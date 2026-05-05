"""Extended Yahoo Finance data collection for 2-3 years of historical data."""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd
import yfinance as yf

from .utils import get_timestamp_filename, save_to_parquet, setup_logging


def ingest_extended_yahoo_data(
    tickers: Optional[List[str]] = None,
    interval: str = "1h",
    period: str = "730d",  # 2 years
    output_dir: Optional[Path] = None,
) -> None:
    """
    Ingest extended historical Yahoo Finance data.
    
    Args:
        tickers: List of ticker symbols (default: AAPL, TSLA, SPY, MSFT, GOOGL, AMZN, NVDA, META, NFLX, AMD)
        interval: Data interval (1h for hourly)
        period: Historical period (730d = 2 years, 1095d = 3 years)
        output_dir: Output directory for parquet files
    """
    logger = setup_logging("yahoo_extended")
    
    if tickers is None:
        tickers = ["AAPL", "TSLA", "SPY", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "NFLX", "AMD"]
    
    if output_dir is None:
        output_dir = Path("data/raw/yahoo")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting extended Yahoo Finance data ingestion for {len(tickers)} tickers")
    logger.info(f"Period: {period}, Interval: {interval}")
    
    success_count = 0
    failed_tickers = []
    
    for ticker in tickers:
        try:
            logger.info(f"Fetching extended data for {ticker}...")
            
            # Download data
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval)
            
            if df.empty:
                logger.warning(f"No data retrieved for {ticker}")
                failed_tickers.append(ticker)
                continue
            
            # Add metadata
            df["ticker"] = ticker
            df["ingested_at"] = datetime.now().isoformat()
            
            # Reset index to make Date a column
            df = df.reset_index()
            
            # Save to parquet with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H")
            filename = f"{ticker}_extended_{timestamp}.parquet"
            filepath = output_dir / filename
            
            save_to_parquet(df, filepath)
            logger.info(f"✓ Saved {len(df)} records for {ticker} to {filename}")
            success_count += 1
            
        except Exception as e:
            logger.error(f"✗ Failed to ingest data for {ticker}: {e}")
            failed_tickers.append(ticker)
    
    logger.info(f"Extended ingestion complete: {success_count}/{len(tickers)} successful")
    if failed_tickers:
        logger.warning(f"Failed tickers: {', '.join(failed_tickers)}")


if __name__ == "__main__":
    ingest_extended_yahoo_data()
