"""
Unit tests for the Yahoo Finance ingestion module.
"""

import logging
import os
import tempfile
from datetime import datetime
from unittest.mock import patch, MagicMock
import pandas as pd
import pytest

from src.ingestion.yahoo_ingest import ingest_yahoo_data


class TestIngestYahooData:
    """Tests for ingest_yahoo_data function."""
    
    @patch('src.ingestion.yahoo_ingest.yf.Ticker')
    @patch('src.ingestion.yahoo_ingest.save_to_parquet')
    def test_ingests_data_for_single_ticker(self, mock_save, mock_ticker):
        """Test that ingest_yahoo_data processes a single ticker correctly."""
        # Create mock OHLCV data
        mock_df = pd.DataFrame({
            'Open': [150.0, 151.0],
            'High': [152.0, 153.0],
            'Low': [149.0, 150.0],
            'Close': [151.0, 152.0],
            'Volume': [1000000, 1100000]
        }, index=pd.date_range('2024-01-01', periods=2, freq='1h'))
        
        mock_ticker_obj = MagicMock()
        mock_ticker_obj.history.return_value = mock_df
        mock_ticker.return_value = mock_ticker_obj
        
        # Run ingestion
        ingest_yahoo_data(tickers=["AAPL"], interval="1h", period="60d")
        
        # Verify Ticker was called correctly
        mock_ticker.assert_called_once_with("AAPL")
        mock_ticker_obj.history.assert_called_once_with(period="60d", interval="1h")
        
        # Verify save_to_parquet was called
        assert mock_save.call_count == 1
        
        # Verify the DataFrame passed to save_to_parquet has required columns
        saved_df = mock_save.call_args[0][0]
        assert 'ticker' in saved_df.columns
        assert 'ingested_at' in saved_df.columns
        assert saved_df['ticker'].iloc[0] == "AAPL"
    
    @patch('src.ingestion.yahoo_ingest.yf.Ticker')
    @patch('src.ingestion.yahoo_ingest.save_to_parquet')
    def test_ingests_data_for_multiple_tickers(self, mock_save, mock_ticker):
        """Test that ingest_yahoo_data processes multiple tickers."""
        # Create mock OHLCV data
        mock_df = pd.DataFrame({
            'Open': [150.0],
            'High': [152.0],
            'Low': [149.0],
            'Close': [151.0],
            'Volume': [1000000]
        }, index=pd.date_range('2024-01-01', periods=1, freq='1h'))
        
        mock_ticker_obj = MagicMock()
        mock_ticker_obj.history.return_value = mock_df
        mock_ticker.return_value = mock_ticker_obj
        
        # Run ingestion for multiple tickers
        tickers = ["AAPL", "TSLA", "SPY"]
        ingest_yahoo_data(tickers=tickers, interval="1h", period="60d")
        
        # Verify Ticker was called for each ticker
        assert mock_ticker.call_count == len(tickers)
        assert mock_save.call_count == len(tickers)
    
    @patch('src.ingestion.yahoo_ingest.yf.Ticker')
    @patch('src.ingestion.yahoo_ingest.save_to_parquet')
    def test_adds_ticker_column(self, mock_save, mock_ticker):
        """Test that ticker column is added with correct value."""
        mock_df = pd.DataFrame({
            'Open': [150.0],
            'High': [152.0],
            'Low': [149.0],
            'Close': [151.0],
            'Volume': [1000000]
        }, index=pd.date_range('2024-01-01', periods=1, freq='1h'))
        
        mock_ticker_obj = MagicMock()
        mock_ticker_obj.history.return_value = mock_df
        mock_ticker.return_value = mock_ticker_obj
        
        ingest_yahoo_data(tickers=["TSLA"])
        
        # Verify ticker column was added
        saved_df = mock_save.call_args[0][0]
        assert 'ticker' in saved_df.columns
        assert all(saved_df['ticker'] == "TSLA")
    
    @patch('src.ingestion.yahoo_ingest.yf.Ticker')
    @patch('src.ingestion.yahoo_ingest.save_to_parquet')
    def test_adds_ingested_at_column_with_iso8601_format(self, mock_save, mock_ticker):
        """Test that ingested_at column is added with ISO 8601 timestamp."""
        mock_df = pd.DataFrame({
            'Open': [150.0],
            'High': [152.0],
            'Low': [149.0],
            'Close': [151.0],
            'Volume': [1000000]
        }, index=pd.date_range('2024-01-01', periods=1, freq='1h'))
        
        mock_ticker_obj = MagicMock()
        mock_ticker_obj.history.return_value = mock_df
        mock_ticker.return_value = mock_ticker_obj
        
        ingest_yahoo_data(tickers=["AAPL"])
        
        # Verify ingested_at column was added
        saved_df = mock_save.call_args[0][0]
        assert 'ingested_at' in saved_df.columns
        
        # Verify ISO 8601 format (should be parseable)
        timestamp_str = saved_df['ingested_at'].iloc[0]
        parsed_timestamp = datetime.fromisoformat(timestamp_str)
        assert isinstance(parsed_timestamp, datetime)
    
    @patch('src.ingestion.yahoo_ingest.yf.Ticker')
    @patch('src.ingestion.yahoo_ingest.save_to_parquet')
    def test_uses_correct_output_path(self, mock_save, mock_ticker):
        """Test that output path follows the required format."""
        mock_df = pd.DataFrame({
            'Open': [150.0],
            'High': [152.0],
            'Low': [149.0],
            'Close': [151.0],
            'Volume': [1000000]
        }, index=pd.date_range('2024-01-01', periods=1, freq='1h'))
        
        mock_ticker_obj = MagicMock()
        mock_ticker_obj.history.return_value = mock_df
        mock_ticker.return_value = mock_ticker_obj
        
        ingest_yahoo_data(tickers=["AAPL"])
        
        # Verify output path (normalize for cross-platform compatibility)
        output_path = mock_save.call_args[0][1]
        normalized_path = output_path.replace('\\', '/')
        assert normalized_path.startswith("data/raw/yahoo/")
        assert "AAPL_" in output_path
        assert output_path.endswith(".parquet")
    
    @patch('src.ingestion.yahoo_ingest.yf.Ticker')
    @patch('src.ingestion.yahoo_ingest.save_to_parquet')
    def test_continues_on_ticker_failure(self, mock_save, mock_ticker, caplog):
        """Test that ingestion continues when a ticker fails."""
        # First ticker succeeds
        mock_df = pd.DataFrame({
            'Open': [150.0],
            'High': [152.0],
            'Low': [149.0],
            'Close': [151.0],
            'Volume': [1000000]
        }, index=pd.date_range('2024-01-01', periods=1, freq='1h'))
        
        # Second ticker fails, third succeeds
        mock_ticker_obj_success = MagicMock()
        mock_ticker_obj_success.history.return_value = mock_df
        
        mock_ticker_obj_fail = MagicMock()
        mock_ticker_obj_fail.history.side_effect = Exception("API error")
        
        # Configure mock to return different objects for different tickers
        def ticker_side_effect(symbol):
            if symbol == "INVALID":
                return mock_ticker_obj_fail
            return mock_ticker_obj_success
        
        mock_ticker.side_effect = ticker_side_effect
        
        with caplog.at_level(logging.ERROR):
            ingest_yahoo_data(tickers=["AAPL", "INVALID", "SPY"])
        
        # Verify that save was called twice (for AAPL and SPY, not INVALID)
        assert mock_save.call_count == 2
        
        # Verify error was logged
        assert any("Failed to ingest data for INVALID" in record.message for record in caplog.records)
    
    @patch('src.ingestion.yahoo_ingest.yf.Ticker')
    @patch('src.ingestion.yahoo_ingest.save_to_parquet')
    def test_handles_empty_dataframe(self, mock_save, mock_ticker, caplog):
        """Test that empty DataFrames are handled gracefully."""
        # Return empty DataFrame
        mock_df = pd.DataFrame()
        
        mock_ticker_obj = MagicMock()
        mock_ticker_obj.history.return_value = mock_df
        mock_ticker.return_value = mock_ticker_obj
        
        with caplog.at_level(logging.WARNING):
            ingest_yahoo_data(tickers=["AAPL"])
        
        # Verify save was not called for empty data
        mock_save.assert_not_called()
        
        # Verify warning was logged
        assert any("No data retrieved for AAPL" in record.message for record in caplog.records)
    
    @patch('src.ingestion.yahoo_ingest.yf.Ticker')
    @patch('src.ingestion.yahoo_ingest.save_to_parquet')
    def test_logs_start_event(self, mock_save, mock_ticker, caplog):
        """Test that start event is logged."""
        mock_df = pd.DataFrame({
            'Open': [150.0],
            'High': [152.0],
            'Low': [149.0],
            'Close': [151.0],
            'Volume': [1000000]
        }, index=pd.date_range('2024-01-01', periods=1, freq='1h'))
        
        mock_ticker_obj = MagicMock()
        mock_ticker_obj.history.return_value = mock_df
        mock_ticker.return_value = mock_ticker_obj
        
        with caplog.at_level(logging.INFO):
            ingest_yahoo_data(tickers=["AAPL"])
        
        # Verify start event was logged
        assert any("Starting Yahoo Finance ingestion" in record.message for record in caplog.records)
    
    @patch('src.ingestion.yahoo_ingest.yf.Ticker')
    @patch('src.ingestion.yahoo_ingest.save_to_parquet')
    def test_logs_completion_with_row_count(self, mock_save, mock_ticker, caplog):
        """Test that completion event is logged with row count."""
        mock_df = pd.DataFrame({
            'Open': [150.0, 151.0, 152.0],
            'High': [152.0, 153.0, 154.0],
            'Low': [149.0, 150.0, 151.0],
            'Close': [151.0, 152.0, 153.0],
            'Volume': [1000000, 1100000, 1200000]
        }, index=pd.date_range('2024-01-01', periods=3, freq='1h'))
        
        mock_ticker_obj = MagicMock()
        mock_ticker_obj.history.return_value = mock_df
        mock_ticker.return_value = mock_ticker_obj
        
        with caplog.at_level(logging.INFO):
            ingest_yahoo_data(tickers=["AAPL"])
        
        # Verify completion event was logged with row count
        assert any("Completed ingestion for AAPL: 3 rows" in record.message for record in caplog.records)
    
    @patch('src.ingestion.yahoo_ingest.yf.Ticker')
    @patch('src.ingestion.yahoo_ingest.save_to_parquet')
    def test_uses_default_parameters(self, mock_save, mock_ticker):
        """Test that default parameters are used when not specified."""
        mock_df = pd.DataFrame({
            'Open': [150.0],
            'High': [152.0],
            'Low': [149.0],
            'Close': [151.0],
            'Volume': [1000000]
        }, index=pd.date_range('2024-01-01', periods=1, freq='1h'))
        
        mock_ticker_obj = MagicMock()
        mock_ticker_obj.history.return_value = mock_df
        mock_ticker.return_value = mock_ticker_obj
        
        # Call without parameters
        ingest_yahoo_data()
        
        # Verify default tickers were used
        assert mock_ticker.call_count == 3  # Default: ["AAPL", "TSLA", "SPY"]
        
        # Verify default interval and period were used
        mock_ticker_obj.history.assert_called_with(period="60d", interval="1h")
