"""
Integration tests for Yahoo Finance ingestion module.

These tests use the real yfinance API with small data samples to verify
end-to-end functionality.
"""

import glob
import os
import shutil
import tempfile
from datetime import datetime
import pandas as pd
import pytest

from src.ingestion.yahoo_ingest import ingest_yahoo_data


class TestYahooIntegration:
    """Integration tests for Yahoo Finance data ingestion."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up test environment and clean up after each test."""
        # Store original directory
        self.original_cwd = os.getcwd()
        
        # Create temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        self.test_data_dir = os.path.join(self.test_dir, "data", "raw", "yahoo")
        os.makedirs(self.test_data_dir, exist_ok=True)
        
        # Change to test directory
        os.chdir(self.test_dir)
        
        yield
        
        # Clean up: change back to original directory and remove test directory
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_end_to_end_execution_with_real_api(self):
        """
        Test end-to-end execution with real yfinance API.
        
        Validates Requirements 1.1-1.9, 8.1-8.5:
        - Retrieves OHLCV data from Yahoo Finance
        - Adds ticker and ingested_at columns
        - Saves to Parquet format in correct directory
        - Preserves data types
        """
        # Execute ingestion with small sample (1 day of data)
        ingest_yahoo_data(tickers=["AAPL"], interval="1h", period="1d")
        
        # Verify Parquet file was created in data/raw/yahoo/
        parquet_files = glob.glob("data/raw/yahoo/AAPL_*.parquet")
        assert len(parquet_files) > 0, "No Parquet file was created"
        
        # Read the Parquet file
        parquet_file = parquet_files[0]
        df = pd.read_parquet(parquet_file)
        
        # Verify file contains required columns
        assert 'ticker' in df.columns, "Missing 'ticker' column"
        assert 'ingested_at' in df.columns, "Missing 'ingested_at' column"
        
        # Verify ticker column has correct value
        assert all(df['ticker'] == "AAPL"), "Ticker column has incorrect values"
        
        # Verify ingested_at is in ISO 8601 format
        ingested_at_value = df['ingested_at'].iloc[0]
        assert isinstance(ingested_at_value, str), "ingested_at should be a string"
        # Verify it can be parsed as ISO 8601
        parsed_timestamp = datetime.fromisoformat(ingested_at_value)
        assert isinstance(parsed_timestamp, datetime), "ingested_at is not valid ISO 8601 format"
        
        # Verify OHLCV columns exist
        expected_ohlcv_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in expected_ohlcv_columns:
            assert col in df.columns, f"Missing OHLCV column: {col}"
        
        # Verify data types are preserved in Parquet format
        assert pd.api.types.is_float_dtype(df['Open']), "Open column should be float"
        assert pd.api.types.is_float_dtype(df['High']), "High column should be float"
        assert pd.api.types.is_float_dtype(df['Low']), "Low column should be float"
        assert pd.api.types.is_float_dtype(df['Close']), "Close column should be float"
        assert pd.api.types.is_integer_dtype(df['Volume']), "Volume column should be integer"
        assert pd.api.types.is_string_dtype(df['ticker']), "ticker column should be string"
        assert pd.api.types.is_string_dtype(df['ingested_at']), "ingested_at column should be string"
        
        # Verify index is datetime (from yfinance)
        assert isinstance(df.index, pd.DatetimeIndex), "Index should be DatetimeIndex"
        
        # Verify we got some data (at least 1 row)
        assert len(df) > 0, "DataFrame should contain at least one row of data"
    
    def test_multiple_tickers_create_separate_files(self):
        """
        Test that multiple tickers create separate Parquet files.
        
        Validates Requirements 1.1, 1.4, 1.6:
        - Each ticker gets its own file
        - Files follow naming convention {ticker}_{YYYYMMDD_HH}.parquet
        """
        # Execute ingestion for multiple tickers
        ingest_yahoo_data(tickers=["AAPL", "SPY"], interval="1h", period="1d")
        
        # Verify separate files were created for each ticker
        aapl_files = glob.glob("data/raw/yahoo/AAPL_*.parquet")
        spy_files = glob.glob("data/raw/yahoo/SPY_*.parquet")
        
        assert len(aapl_files) > 0, "No Parquet file created for AAPL"
        assert len(spy_files) > 0, "No Parquet file created for SPY"
        
        # Verify each file contains the correct ticker
        aapl_df = pd.read_parquet(aapl_files[0])
        spy_df = pd.read_parquet(spy_files[0])
        
        assert all(aapl_df['ticker'] == "AAPL"), "AAPL file contains wrong ticker"
        assert all(spy_df['ticker'] == "SPY"), "SPY file contains wrong ticker"
    
    def test_file_naming_convention(self):
        """
        Test that files follow the naming convention {ticker}_{YYYYMMDD_HH}.parquet.
        
        Validates Requirement 1.6:
        - File naming follows specified format
        """
        # Execute ingestion
        ingest_yahoo_data(tickers=["AAPL"], interval="1h", period="1d")
        
        # Get created file
        parquet_files = glob.glob("data/raw/yahoo/AAPL_*.parquet")
        assert len(parquet_files) > 0, "No Parquet file was created"
        
        # Verify filename format
        filename = os.path.basename(parquet_files[0])
        
        # Should be in format: AAPL_YYYYMMDD_HH.parquet
        assert filename.startswith("AAPL_"), "Filename should start with ticker"
        assert filename.endswith(".parquet"), "Filename should end with .parquet"
        
        # Extract timestamp part (between ticker and .parquet)
        timestamp_part = filename[5:-8]  # Remove "AAPL_" and ".parquet"
        
        # Verify timestamp format (YYYYMMDD_HH)
        assert len(timestamp_part) == 11, f"Timestamp should be 11 characters (YYYYMMDD_HH), got {len(timestamp_part)}"
        assert timestamp_part[8] == "_", "Timestamp should have underscore between date and hour"
        
        # Verify it's a valid date/time
        date_part = timestamp_part[:8]
        hour_part = timestamp_part[9:]
        
        # Should be able to parse as date
        datetime.strptime(date_part, "%Y%m%d")
        
        # Hour should be 00-23
        hour = int(hour_part)
        assert 0 <= hour <= 23, f"Hour should be 00-23, got {hour}"
    
    def test_idempotent_execution(self):
        """
        Test that re-running ingestion within the same hour overwrites the file.
        
        Validates Requirement 1.7:
        - Multiple executions produce consistent results without duplication
        """
        # First execution
        ingest_yahoo_data(tickers=["AAPL"], interval="1h", period="1d")
        
        # Get files after first execution
        files_after_first = glob.glob("data/raw/yahoo/AAPL_*.parquet")
        assert len(files_after_first) == 1, "Should have exactly one file after first execution"
        
        first_file = files_after_first[0]
        first_df = pd.read_parquet(first_file)
        first_row_count = len(first_df)
        
        # Second execution (same hour)
        ingest_yahoo_data(tickers=["AAPL"], interval="1h", period="1d")
        
        # Get files after second execution
        files_after_second = glob.glob("data/raw/yahoo/AAPL_*.parquet")
        
        # Should still have exactly one file (overwritten, not appended)
        assert len(files_after_second) == 1, "Should still have exactly one file after second execution"
        
        # Verify it's the same filename (same hour)
        assert files_after_second[0] == first_file, "Filename should be the same (same hour)"
        
        # Verify data is consistent (not duplicated)
        second_df = pd.read_parquet(files_after_second[0])
        second_row_count = len(second_df)
        
        # Row count should be similar (not doubled)
        # Allow some variance due to API returning slightly different data
        assert abs(second_row_count - first_row_count) < 10, \
            f"Row count changed significantly: {first_row_count} -> {second_row_count} (possible duplication)"
    
    def test_handles_api_errors_gracefully(self):
        """
        Test that invalid tickers are handled gracefully without crashing.
        
        Validates Requirement 1.8:
        - API errors are logged and processing continues
        """
        # Execute with mix of valid and invalid tickers
        # Note: yfinance may return empty data for invalid tickers rather than error
        ingest_yahoo_data(tickers=["AAPL", "INVALID_TICKER_XYZ"], interval="1h", period="1d")
        
        # Verify AAPL file was created (valid ticker succeeded)
        aapl_files = glob.glob("data/raw/yahoo/AAPL_*.parquet")
        assert len(aapl_files) > 0, "Valid ticker (AAPL) should have created a file"
        
        # Invalid ticker may or may not create a file (depends on yfinance behavior)
        # The important thing is that the function didn't crash
        # and the valid ticker was processed
