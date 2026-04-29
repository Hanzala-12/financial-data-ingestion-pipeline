"""
Unit tests for the ingestion utilities module.
"""

import logging
import os
import re
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import pytest

from src.ingestion.utils import (
    setup_logging,
    ensure_directory_exists,
    get_timestamp_filename,
    save_to_parquet
)


class TestSetupLogging:
    """Tests for setup_logging function."""
    
    def test_creates_logger_with_correct_name(self):
        """Test that setup_logging creates a logger with the correct name."""
        component_name = "test_component"
        logger = setup_logging(component_name)
        
        assert logger.name == component_name
        assert isinstance(logger, logging.Logger)
    
    def test_logger_has_correct_format(self):
        """Test that the logger has the correct format."""
        logger = setup_logging("test_format")
        
        # Check that handler exists and has correct format
        assert len(logger.handlers) > 0
        handler = logger.handlers[0]
        formatter = handler.formatter
        
        # Verify format string
        expected_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        assert formatter._fmt == expected_format
    
    def test_logger_level_is_info(self):
        """Test that the logger level is set to INFO."""
        logger = setup_logging("test_level")
        assert logger.level == logging.INFO


class TestEnsureDirectoryExists:
    """Tests for ensure_directory_exists function."""
    
    def test_creates_missing_directory(self):
        """Test that ensure_directory_exists creates a missing directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = os.path.join(tmpdir, "test_dir", "nested_dir")
            
            # Verify directory doesn't exist
            assert not os.path.exists(test_path)
            
            # Create directory
            ensure_directory_exists(test_path)
            
            # Verify directory was created
            assert os.path.exists(test_path)
            assert os.path.isdir(test_path)
    
    def test_handles_existing_directory(self):
        """Test that ensure_directory_exists handles existing directories gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Directory already exists
            ensure_directory_exists(tmpdir)
            
            # Should not raise an error
            assert os.path.exists(tmpdir)


class TestGetTimestampFilename:
    """Tests for get_timestamp_filename function."""
    
    def test_generates_correct_format_with_ticker(self):
        """Test filename format with ticker parameter."""
        filename = get_timestamp_filename("yahoo", "AAPL")
        
        # Should match pattern: AAPL_YYYYMMDD_HH.parquet
        pattern = r"^AAPL_\d{8}_\d{2}\.parquet$"
        assert re.match(pattern, filename), f"Filename '{filename}' doesn't match expected pattern"
    
    def test_generates_correct_format_without_ticker(self):
        """Test filename format without ticker parameter."""
        filename = get_timestamp_filename("reuters")
        
        # Should match pattern: reuters_YYYYMMDD_HH.parquet
        pattern = r"^reuters_\d{8}_\d{2}\.parquet$"
        assert re.match(pattern, filename), f"Filename '{filename}' doesn't match expected pattern"
    
    def test_timestamp_format_is_valid(self):
        """Test that the timestamp portion is a valid format."""
        filename = get_timestamp_filename("test", "TSLA")
        
        # Extract timestamp portion (between first underscore and .parquet)
        # Format: TSLA_20240115_14.parquet -> 20240115_14
        parts = filename.replace(".parquet", "").split("_")
        date_part = parts[1]  # YYYYMMDD
        hour_part = parts[2]  # HH
        
        # Verify date part is 8 digits
        assert len(date_part) == 8
        assert date_part.isdigit()
        
        # Verify hour part is 2 digits
        assert len(hour_part) == 2
        assert hour_part.isdigit()
        assert 0 <= int(hour_part) <= 23


class TestSaveToParquet:
    """Tests for save_to_parquet function."""
    
    def test_writes_valid_parquet_file(self):
        """Test that save_to_parquet writes a valid Parquet file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test DataFrame
            df = pd.DataFrame({
                'col1': [1, 2, 3],
                'col2': ['a', 'b', 'c']
            })
            
            filepath = os.path.join(tmpdir, "test.parquet")
            
            # Save to Parquet
            save_to_parquet(df, filepath)
            
            # Verify file exists
            assert os.path.exists(filepath)
            
            # Verify file can be read back
            df_read = pd.read_parquet(filepath)
            pd.testing.assert_frame_equal(df, df_read)
    
    def test_uses_snappy_compression(self):
        """Test that save_to_parquet uses Snappy compression."""
        with tempfile.TemporaryDirectory() as tmpdir:
            df = pd.DataFrame({'col1': [1, 2, 3]})
            filepath = os.path.join(tmpdir, "test.parquet")
            
            save_to_parquet(df, filepath)
            
            # Read metadata to verify compression
            import pyarrow.parquet as pq
            parquet_file = pq.ParquetFile(filepath)
            
            # Check that compression is snappy
            assert parquet_file.metadata.row_group(0).column(0).compression == 'SNAPPY'
    
    def test_creates_directory_if_missing(self):
        """Test that save_to_parquet creates the directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            df = pd.DataFrame({'col1': [1, 2, 3]})
            filepath = os.path.join(tmpdir, "nested", "dir", "test.parquet")
            
            # Directory doesn't exist yet
            assert not os.path.exists(os.path.dirname(filepath))
            
            # Save should create directory
            save_to_parquet(df, filepath)
            
            # Verify file was created
            assert os.path.exists(filepath)
    
    def test_error_handling_on_write_failure(self):
        """Test that save_to_parquet handles write failures gracefully."""
        df = pd.DataFrame({'col1': [1, 2, 3]})
        
        # Use an invalid path that will cause write to fail
        invalid_path = "/invalid/path/that/does/not/exist/test.parquet"
        
        # Should raise an exception
        with pytest.raises(Exception):
            save_to_parquet(df, invalid_path)
    
    def test_logs_success_message(self, caplog):
        """Test that save_to_parquet logs a success message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            df = pd.DataFrame({'col1': [1, 2, 3]})
            filepath = os.path.join(tmpdir, "test.parquet")
            
            with caplog.at_level(logging.INFO):
                save_to_parquet(df, filepath)
            
            # Check that success message was logged
            assert any("Successfully saved" in record.message for record in caplog.records)
            assert any(str(len(df)) in record.message for record in caplog.records)
    
    def test_logs_error_on_failure(self, caplog):
        """Test that save_to_parquet logs an error on failure."""
        df = pd.DataFrame({'col1': [1, 2, 3]})
        invalid_path = "/invalid/path/test.parquet"
        
        with caplog.at_level(logging.ERROR):
            try:
                save_to_parquet(df, invalid_path)
            except Exception:
                pass  # Expected to fail
        
        # Check that error was logged
        assert any("Failed to save data" in record.message for record in caplog.records)
