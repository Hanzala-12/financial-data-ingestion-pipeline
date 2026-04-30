"""
Unit tests for the Reuters RSS feed ingestion module.
"""

import logging
from datetime import datetime
from unittest.mock import patch, MagicMock
import pandas as pd
import pytest

from src.ingestion.reuters_ingest import ingest_reuters_feed


class TestIngestReutersFeed:
    """Tests for ingest_reuters_feed function."""
    
    @patch('src.ingestion.reuters_ingest.feedparser.parse')
    @patch('src.ingestion.reuters_ingest.save_to_parquet')
    def test_ingests_feed_successfully(self, mock_save, mock_parse):
        """Test that ingest_reuters_feed processes RSS feed correctly."""
        # Create mock feed data
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [
            {
                'title': 'Market Update: Stocks Rise',
                'link': 'https://reuters.com/article1',
                'published': '2024-01-15T10:00:00Z'
            },
            {
                'title': 'Tech Sector Analysis',
                'link': 'https://reuters.com/article2',
                'published': '2024-01-15T11:00:00Z'
            }
        ]
        mock_parse.return_value = mock_feed
        
        # Run ingestion
        result = ingest_reuters_feed()
        
        # Verify feedparser was called correctly
        mock_parse.assert_called_once_with("http://feeds.reuters.com/reuters/businessNews")
        
        # Verify save_to_parquet was called
        assert mock_save.call_count == 1
        
        # Verify the DataFrame passed to save_to_parquet has required columns
        saved_df = mock_save.call_args[0][0]
        assert 'title' in saved_df.columns
        assert 'link' in saved_df.columns
        assert 'published_date' in saved_df.columns
        assert 'ingested_at' in saved_df.columns
        
        # Verify data was extracted correctly
        assert len(saved_df) == 2
        assert saved_df['title'].iloc[0] == 'Market Update: Stocks Rise'
        assert saved_df['link'].iloc[0] == 'https://reuters.com/article1'
        assert saved_df['published_date'].iloc[0] == '2024-01-15T10:00:00Z'
        
        # Verify function returns True on success
        assert result is True
    
    @patch('src.ingestion.reuters_ingest.feedparser.parse')
    @patch('src.ingestion.reuters_ingest.save_to_parquet')
    def test_extracts_title_field(self, mock_save, mock_parse):
        """Test that title field is extracted correctly."""
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [
            {
                'title': 'Breaking News: Market Volatility',
                'link': 'https://reuters.com/article1',
                'published': '2024-01-15T10:00:00Z'
            }
        ]
        mock_parse.return_value = mock_feed
        
        ingest_reuters_feed()
        
        saved_df = mock_save.call_args[0][0]
        assert saved_df['title'].iloc[0] == 'Breaking News: Market Volatility'
    
    @patch('src.ingestion.reuters_ingest.feedparser.parse')
    @patch('src.ingestion.reuters_ingest.save_to_parquet')
    def test_extracts_link_field(self, mock_save, mock_parse):
        """Test that link field is extracted correctly."""
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [
            {
                'title': 'Article Title',
                'link': 'https://reuters.com/business/article123',
                'published': '2024-01-15T10:00:00Z'
            }
        ]
        mock_parse.return_value = mock_feed
        
        ingest_reuters_feed()
        
        saved_df = mock_save.call_args[0][0]
        assert saved_df['link'].iloc[0] == 'https://reuters.com/business/article123'
    
    @patch('src.ingestion.reuters_ingest.feedparser.parse')
    @patch('src.ingestion.reuters_ingest.save_to_parquet')
    def test_extracts_published_date_field(self, mock_save, mock_parse):
        """Test that published_date field is extracted correctly."""
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [
            {
                'title': 'Article Title',
                'link': 'https://reuters.com/article1',
                'published': '2024-01-15T14:30:00Z'
            }
        ]
        mock_parse.return_value = mock_feed
        
        ingest_reuters_feed()
        
        saved_df = mock_save.call_args[0][0]
        assert saved_df['published_date'].iloc[0] == '2024-01-15T14:30:00Z'
    
    @patch('src.ingestion.reuters_ingest.feedparser.parse')
    @patch('src.ingestion.reuters_ingest.save_to_parquet')
    def test_adds_ingested_at_column_with_iso8601_format(self, mock_save, mock_parse):
        """Test that ingested_at column is added with ISO 8601 timestamp."""
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [
            {
                'title': 'Article Title',
                'link': 'https://reuters.com/article1',
                'published': '2024-01-15T10:00:00Z'
            }
        ]
        mock_parse.return_value = mock_feed
        
        ingest_reuters_feed()
        
        # Verify ingested_at column was added
        saved_df = mock_save.call_args[0][0]
        assert 'ingested_at' in saved_df.columns
        
        # Verify ISO 8601 format (should be parseable)
        timestamp_str = saved_df['ingested_at'].iloc[0]
        parsed_timestamp = datetime.fromisoformat(timestamp_str)
        assert isinstance(parsed_timestamp, datetime)
    
    @patch('src.ingestion.reuters_ingest.feedparser.parse')
    @patch('src.ingestion.reuters_ingest.save_to_parquet')
    def test_uses_correct_output_path(self, mock_save, mock_parse):
        """Test that output path follows the required format."""
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [
            {
                'title': 'Article Title',
                'link': 'https://reuters.com/article1',
                'published': '2024-01-15T10:00:00Z'
            }
        ]
        mock_parse.return_value = mock_feed
        
        ingest_reuters_feed()
        
        # Verify output path (normalize for cross-platform compatibility)
        output_path = mock_save.call_args[0][1]
        normalized_path = output_path.replace('\\', '/')
        assert normalized_path.startswith("data/raw/reuters/")
        assert "reuters_" in output_path
        assert output_path.endswith(".parquet")
    
    @patch('src.ingestion.reuters_ingest.feedparser.parse')
    @patch('src.ingestion.reuters_ingest.save_to_parquet')
    def test_handles_feed_unavailable_error(self, mock_save, mock_parse, caplog):
        """Test that feed unavailable error is handled gracefully."""
        # Simulate feed parsing error
        mock_feed = MagicMock()
        mock_feed.bozo = True
        mock_feed.bozo_exception = Exception("Feed unavailable")
        mock_feed.entries = []
        mock_parse.return_value = mock_feed
        
        with caplog.at_level(logging.ERROR):
            result = ingest_reuters_feed()
        
        # Verify save was not called
        mock_save.assert_not_called()
        
        # Verify error was logged
        assert any("Feed parsing error" in record.message for record in caplog.records)
        
        # Verify function returns False on error
        assert result is False
    
    @patch('src.ingestion.reuters_ingest.feedparser.parse')
    @patch('src.ingestion.reuters_ingest.save_to_parquet')
    def test_handles_empty_feed(self, mock_save, mock_parse, caplog):
        """Test that empty feed is handled gracefully."""
        # Simulate empty feed
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = []
        mock_parse.return_value = mock_feed
        
        with caplog.at_level(logging.WARNING):
            result = ingest_reuters_feed()
        
        # Verify save was not called
        mock_save.assert_not_called()
        
        # Verify warning was logged
        assert any("No entries found in RSS feed" in record.message for record in caplog.records)
        
        # Verify function returns False
        assert result is False
    
    @patch('src.ingestion.reuters_ingest.feedparser.parse')
    @patch('src.ingestion.reuters_ingest.save_to_parquet')
    def test_handles_exception_during_ingestion(self, mock_save, mock_parse, caplog):
        """Test that exceptions during ingestion are handled gracefully."""
        # Simulate exception during parsing
        mock_parse.side_effect = Exception("Network error")
        
        with caplog.at_level(logging.ERROR):
            result = ingest_reuters_feed()
        
        # Verify error was logged
        assert any("Failed to ingest Reuters feed" in record.message for record in caplog.records)
        
        # Verify function returns False on exception
        assert result is False
    
    @patch('src.ingestion.reuters_ingest.feedparser.parse')
    @patch('src.ingestion.reuters_ingest.save_to_parquet')
    def test_logs_start_event(self, mock_save, mock_parse, caplog):
        """Test that start event is logged."""
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [
            {
                'title': 'Article Title',
                'link': 'https://reuters.com/article1',
                'published': '2024-01-15T10:00:00Z'
            }
        ]
        mock_parse.return_value = mock_feed
        
        with caplog.at_level(logging.INFO):
            ingest_reuters_feed()
        
        # Verify start event was logged
        assert any("Starting Reuters RSS feed ingestion" in record.message for record in caplog.records)
    
    @patch('src.ingestion.reuters_ingest.feedparser.parse')
    @patch('src.ingestion.reuters_ingest.save_to_parquet')
    def test_logs_completion_with_row_count(self, mock_save, mock_parse, caplog):
        """Test that completion event is logged with row count."""
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [
            {
                'title': 'Article 1',
                'link': 'https://reuters.com/article1',
                'published': '2024-01-15T10:00:00Z'
            },
            {
                'title': 'Article 2',
                'link': 'https://reuters.com/article2',
                'published': '2024-01-15T11:00:00Z'
            },
            {
                'title': 'Article 3',
                'link': 'https://reuters.com/article3',
                'published': '2024-01-15T12:00:00Z'
            }
        ]
        mock_parse.return_value = mock_feed
        
        with caplog.at_level(logging.INFO):
            ingest_reuters_feed()
        
        # Verify completion event was logged with row count
        assert any("Completed Reuters ingestion: 3 rows" in record.message for record in caplog.records)
    
    @patch('src.ingestion.reuters_ingest.feedparser.parse')
    @patch('src.ingestion.reuters_ingest.save_to_parquet')
    def test_uses_custom_feed_url(self, mock_save, mock_parse):
        """Test that custom feed URL can be provided."""
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [
            {
                'title': 'Article Title',
                'link': 'https://reuters.com/article1',
                'published': '2024-01-15T10:00:00Z'
            }
        ]
        mock_parse.return_value = mock_feed
        
        custom_url = "http://custom.feed.url/rss"
        ingest_reuters_feed(feed_url=custom_url)
        
        # Verify custom URL was used
        mock_parse.assert_called_once_with(custom_url)
    
    @patch('src.ingestion.reuters_ingest.feedparser.parse')
    @patch('src.ingestion.reuters_ingest.save_to_parquet')
    def test_handles_missing_fields_gracefully(self, mock_save, mock_parse):
        """Test that missing fields in entries are handled with empty strings."""
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [
            {
                'title': 'Article with missing fields'
                # Missing 'link' and 'published'
            }
        ]
        mock_parse.return_value = mock_feed
        
        ingest_reuters_feed()
        
        # Verify DataFrame was created with empty strings for missing fields
        saved_df = mock_save.call_args[0][0]
        assert saved_df['title'].iloc[0] == 'Article with missing fields'
        assert saved_df['link'].iloc[0] == ''
        assert saved_df['published_date'].iloc[0] == ''
