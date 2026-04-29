"""
Shared utilities for the financial data ingestion pipeline.

This module provides common functionality for logging, file operations,
timestamp generation, and Parquet file handling.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
import pandas as pd


def setup_logging(component_name: str) -> logging.Logger:
    """
    Configure logging for a component.
    
    Args:
        component_name: Name to include in log messages
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(component_name)
    logger.setLevel(logging.INFO)
    
    # Only add handler if logger doesn't already have one
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


def ensure_directory_exists(path: str) -> None:
    """
    Create directory if it doesn't exist.
    
    Args:
        path: Directory path to create
    """
    Path(path).mkdir(parents=True, exist_ok=True)


def get_timestamp_filename(source: str, ticker: str = None) -> str:
    """
    Generate timestamp-based filename for idempotent writes.
    
    Args:
        source: Data source name (e.g., "yahoo", "reuters")
        ticker: Optional ticker symbol for per-ticker files
    
    Returns:
        Filename in format {source}_{YYYYMMDD_HH}.parquet or {ticker}_{YYYYMMDD_HH}.parquet
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H")
    
    if ticker:
        return f"{ticker}_{timestamp}.parquet"
    else:
        return f"{source}_{timestamp}.parquet"


def save_to_parquet(df: pd.DataFrame, filepath: str) -> None:
    """
    Save DataFrame to Parquet with Snappy compression.
    
    Args:
        df: DataFrame to save
        filepath: Output file path
    
    Raises:
        Exception: Logs error if write fails
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Ensure the directory exists
        directory = os.path.dirname(filepath)
        if directory:
            ensure_directory_exists(directory)
        
        # Write to Parquet with Snappy compression
        df.to_parquet(
            filepath,
            engine='pyarrow',
            compression='snappy',
            index=True
        )
        logger.info(f"Successfully saved {len(df)} rows to {filepath}")
    except Exception as e:
        logger.error(f"Failed to save data to {filepath}: {e}", exc_info=True)
        raise
