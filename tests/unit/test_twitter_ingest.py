"""
Unit tests for the Twitter ingestion module.
"""

import logging
import os
from datetime import datetime
from unittest.mock import patch, MagicMock
import pandas as pd
import pytest

from src.ingestion.twitter_ingest import ingest_twitter_cashtags


class TestIngestTwitterCashtags:
    """Tests for ingest_twitter_cashtags function."""
    
    @patch('src.ingestion.twitter_ingest.sntwitter.TwitterSearchScraper')
    @patch('src.ingestion.twitter_ingest.save_to_parquet')
    def test_ingests_tweets_for_single_cashtag(self, mock_save, mock_scraper_class):
        """Test that ingest_twitter_cashtags processes a single cashtag correctly."""
        # Create mock tweet objects
        mock_tweet1 = MagicMock()
        mock_tweet1.rawContent = "Great news for $AAPL today!"
        mock_tweet1.date = datetime(2024, 1, 15, 10, 30)
        mock_tweet1.likeCount = 42
        mock_tweet1.retweetCount = 10
        
        mock_tweet2 = MagicMock()
        mock_tweet2.rawContent = "$AAPL to the moon!"
        mock_tweet2.date = datetime(2024, 1, 15, 11, 0)
        mock_tweet2.likeCount = 100
        mock_tweet2.retweetCount = 25
        
        # Configure mock scraper
        mock_scraper = MagicMock()
        mock_scraper.get_items.return_value = iter([mock_tweet1, mock_tweet2])
        mock_scraper_class.return_value = mock_scraper
        
        # Run ingestion
        ingest_twitter_cashtags(cashtags=["$AAPL"], limit=100)
        
        # Verify scraper was called correctly
        mock_scraper_class.assert_called_once_with("$AAPL")
        
        # Verify save_to_parquet was called
        assert mock_save.call_count == 1
        
        # Verify the DataFrame passed to save_to_parquet has required columns
        saved_df = mock_save.call_args[0][0]
        assert 'text' in saved_df.columns
        assert 'created_at' in saved_df.columns
        assert 'likes' in saved_df.columns
        assert 'retweets' in saved_df.columns
        assert 'cashtag' in saved_df.columns
        assert 'ingested_at' in saved_df.columns
        
        # Verify data content
        assert len(saved_df) == 2
        assert saved_df['cashtag'].iloc[0] == "$AAPL"
    
    @patch('src.ingestion.twitter_ingest.sntwitter.TwitterSearchScraper')
    @patch('src.ingestion.twitter_ingest.save_to_parquet')
    def test_ingests_tweets_for_multiple_cashtags(self, mock_save, mock_scraper_class):
        """Test that ingest_twitter_cashtags processes multiple cashtags."""
        # Create mock tweets for each cashtag
        def create_mock_tweet(text):
            mock_tweet = MagicMock()
            mock_tweet.rawContent = text
            mock_tweet.date = datetime(2024, 1, 15, 10, 30)
            mock_tweet.likeCount = 10
            mock_tweet.retweetCount = 2
            return mock_tweet
        
        # Configure mock scraper to return fresh iterator each time
        def scraper_side_effect(cashtag):
            mock_scraper = MagicMock()
            mock_scraper.get_items.return_value = iter([create_mock_tweet(f"Tweet about {cashtag}")])
            return mock_scraper
        
        mock_scraper_class.side_effect = scraper_side_effect
        
        # Run ingestion for multiple cashtags
        cashtags = ["$AAPL", "$TSLA"]
        ingest_twitter_cashtags(cashtags=cashtags, limit=100)
        
        # Verify scraper was called for each cashtag
        assert mock_scraper_class.call_count == len(cashtags)
        
        # Verify save was called once (all tweets in one file)
        assert mock_save.call_count == 1
        
        # Verify DataFrame contains tweets from both cashtags
        saved_df = mock_save.call_args[0][0]
        assert len(saved_df) == 2  # One tweet per cashtag
    
    @patch('src.ingestion.twitter_ingest.sntwitter.TwitterSearchScraper')
    @patch('src.ingestion.twitter_ingest.save_to_parquet')
    def test_extracts_text_field(self, mock_save, mock_scraper_class):
        """Test that tweet text is extracted correctly."""
        mock_tweet = MagicMock()
        mock_tweet.rawContent = "This is a test tweet about $AAPL"
        mock_tweet.date = datetime(2024, 1, 15, 10, 30)
        mock_tweet.likeCount = 5
        mock_tweet.retweetCount = 1
        
        mock_scraper = MagicMock()
        mock_scraper.get_items.return_value = iter([mock_tweet])
        mock_scraper_class.return_value = mock_scraper
        
        ingest_twitter_cashtags(cashtags=["$AAPL"])
        
        saved_df = mock_save.call_args[0][0]
        assert saved_df['text'].iloc[0] == "This is a test tweet about $AAPL"
    
    @patch('src.ingestion.twitter_ingest.sntwitter.TwitterSearchScraper')
    @patch('src.ingestion.twitter_ingest.save_to_parquet')
    def test_extracts_created_at_field(self, mock_save, mock_scraper_class):
        """Test that tweet timestamp is extracted correctly."""
        mock_tweet = MagicMock()
        mock_tweet.rawContent = "Test tweet"
        mock_tweet.date = datetime(2024, 1, 15, 10, 30, 45)
        mock_tweet.likeCount = 5
        mock_tweet.retweetCount = 1
        
        mock_scraper = MagicMock()
        mock_scraper.get_items.return_value = iter([mock_tweet])
        mock_scraper_class.return_value = mock_scraper
        
        ingest_twitter_cashtags(cashtags=["$AAPL"])
        
        saved_df = mock_save.call_args[0][0]
        assert saved_df['created_at'].iloc[0] == "2024-01-15T10:30:45"
    
    @patch('src.ingestion.twitter_ingest.sntwitter.TwitterSearchScraper')
    @patch('src.ingestion.twitter_ingest.save_to_parquet')
    def test_extracts_likes_field(self, mock_save, mock_scraper_class):
        """Test that like count is extracted correctly."""
        mock_tweet = MagicMock()
        mock_tweet.rawContent = "Test tweet"
        mock_tweet.date = datetime(2024, 1, 15, 10, 30)
        mock_tweet.likeCount = 42
        mock_tweet.retweetCount = 1
        
        mock_scraper = MagicMock()
        mock_scraper.get_items.return_value = iter([mock_tweet])
        mock_scraper_class.return_value = mock_scraper
        
        ingest_twitter_cashtags(cashtags=["$AAPL"])
        
        saved_df = mock_save.call_args[0][0]
        assert saved_df['likes'].iloc[0] == 42
    
    @patch('src.ingestion.twitter_ingest.sntwitter.TwitterSearchScraper')
    @patch('src.ingestion.twitter_ingest.save_to_parquet')
    def test_extracts_retweets_field(self, mock_save, mock_scraper_class):
        """Test that retweet count is extracted correctly."""
        mock_tweet = MagicMock()
        mock_tweet.rawContent = "Test tweet"
        mock_tweet.date = datetime(2024, 1, 15, 10, 30)
        mock_tweet.likeCount = 5
        mock_tweet.retweetCount = 15
        
        mock_scraper = MagicMock()
        mock_scraper.get_items.return_value = iter([mock_tweet])
        mock_scraper_class.return_value = mock_scraper
        
        ingest_twitter_cashtags(cashtags=["$AAPL"])
        
        saved_df = mock_save.call_args[0][0]
        assert saved_df['retweets'].iloc[0] == 15
    
    @patch('src.ingestion.twitter_ingest.sntwitter.TwitterSearchScraper')
    @patch('src.ingestion.twitter_ingest.save_to_parquet')
    def test_adds_cashtag_column(self, mock_save, mock_scraper_class):
        """Test that cashtag column is added with correct value."""
        mock_tweet = MagicMock()
        mock_tweet.rawContent = "Test tweet"
        mock_tweet.date = datetime(2024, 1, 15, 10, 30)
        mock_tweet.likeCount = 5
        mock_tweet.retweetCount = 1
        
        mock_scraper = MagicMock()
        mock_scraper.get_items.return_value = iter([mock_tweet])
        mock_scraper_class.return_value = mock_scraper
        
        ingest_twitter_cashtags(cashtags=["$TSLA"])
        
        saved_df = mock_save.call_args[0][0]
        assert 'cashtag' in saved_df.columns
        assert saved_df['cashtag'].iloc[0] == "$TSLA"
    
    @patch('src.ingestion.twitter_ingest.sntwitter.TwitterSearchScraper')
    @patch('src.ingestion.twitter_ingest.save_to_parquet')
    def test_adds_ingested_at_column_with_iso8601_format(self, mock_save, mock_scraper_class):
        """Test that ingested_at column is added with ISO 8601 timestamp."""
        mock_tweet = MagicMock()
        mock_tweet.rawContent = "Test tweet"
        mock_tweet.date = datetime(2024, 1, 15, 10, 30)
        mock_tweet.likeCount = 5
        mock_tweet.retweetCount = 1
        
        mock_scraper = MagicMock()
        mock_scraper.get_items.return_value = iter([mock_tweet])
        mock_scraper_class.return_value = mock_scraper
        
        ingest_twitter_cashtags(cashtags=["$AAPL"])
        
        saved_df = mock_save.call_args[0][0]
        assert 'ingested_at' in saved_df.columns
        
        # Verify ISO 8601 format (should be parseable)
        timestamp_str = saved_df['ingested_at'].iloc[0]
        parsed_timestamp = datetime.fromisoformat(timestamp_str)
        assert isinstance(parsed_timestamp, datetime)
    
    @patch('src.ingestion.twitter_ingest.sntwitter.TwitterSearchScraper')
    @patch('src.ingestion.twitter_ingest.save_to_parquet')
    def test_uses_correct_output_path(self, mock_save, mock_scraper_class):
        """Test that output path follows the required format."""
        mock_tweet = MagicMock()
        mock_tweet.rawContent = "Test tweet"
        mock_tweet.date = datetime(2024, 1, 15, 10, 30)
        mock_tweet.likeCount = 5
        mock_tweet.retweetCount = 1
        
        mock_scraper = MagicMock()
        mock_scraper.get_items.return_value = iter([mock_tweet])
        mock_scraper_class.return_value = mock_scraper
        
        ingest_twitter_cashtags(cashtags=["$AAPL"])
        
        # Verify output path (normalize for cross-platform compatibility)
        output_path = mock_save.call_args[0][1]
        normalized_path = output_path.replace('\\', '/')
        assert normalized_path.startswith("data/raw/twitter/")
        assert "twitter_" in output_path
        assert output_path.endswith(".parquet")
    
    @patch('src.ingestion.twitter_ingest.sntwitter.TwitterSearchScraper')
    @patch('src.ingestion.twitter_ingest.save_to_parquet')
    def test_respects_limit_parameter(self, mock_save, mock_scraper_class):
        """Test that the limit parameter is respected."""
        # Create more tweets than the limit
        mock_tweets = []
        for i in range(10):
            mock_tweet = MagicMock()
            mock_tweet.rawContent = f"Tweet {i}"
            mock_tweet.date = datetime(2024, 1, 15, 10, i)
            mock_tweet.likeCount = i
            mock_tweet.retweetCount = i
            mock_tweets.append(mock_tweet)
        
        mock_scraper = MagicMock()
        mock_scraper.get_items.return_value = iter(mock_tweets)
        mock_scraper_class.return_value = mock_scraper
        
        # Set limit to 5
        ingest_twitter_cashtags(cashtags=["$AAPL"], limit=5)
        
        # Verify only 5 tweets were saved
        saved_df = mock_save.call_args[0][0]
        assert len(saved_df) == 5
    
    @patch('src.ingestion.twitter_ingest.sntwitter.TwitterSearchScraper')
    @patch('src.ingestion.twitter_ingest.save_to_parquet')
    def test_continues_on_cashtag_failure(self, mock_save, mock_scraper_class, caplog):
        """Test that ingestion continues when a cashtag fails."""
        # First cashtag succeeds
        mock_tweet = MagicMock()
        mock_tweet.rawContent = "Test tweet"
        mock_tweet.date = datetime(2024, 1, 15, 10, 30)
        mock_tweet.likeCount = 5
        mock_tweet.retweetCount = 1
        
        mock_scraper_success = MagicMock()
        mock_scraper_success.get_items.return_value = iter([mock_tweet])
        
        # Second cashtag fails
        mock_scraper_fail = MagicMock()
        mock_scraper_fail.get_items.side_effect = Exception("Scraping error")
        
        # Configure mock to return different scrapers
        def scraper_side_effect(cashtag):
            if cashtag == "$INVALID":
                return mock_scraper_fail
            return mock_scraper_success
        
        mock_scraper_class.side_effect = scraper_side_effect
        
        with caplog.at_level(logging.ERROR):
            ingest_twitter_cashtags(cashtags=["$AAPL", "$INVALID", "$TSLA"])
        
        # Verify that save was called once (with tweets from AAPL and TSLA)
        assert mock_save.call_count == 1
        
        # Verify error was logged
        assert any("Failed to scrape tweets for $INVALID" in record.message for record in caplog.records)
    
    @patch('src.ingestion.twitter_ingest.sntwitter.TwitterSearchScraper')
    @patch('src.ingestion.twitter_ingest.save_to_parquet')
    def test_handles_no_tweets_for_cashtag(self, mock_save, mock_scraper_class, caplog):
        """Test that empty results are handled gracefully."""
        # Return empty iterator
        mock_scraper = MagicMock()
        mock_scraper.get_items.return_value = iter([])
        mock_scraper_class.return_value = mock_scraper
        
        with caplog.at_level(logging.WARNING):
            ingest_twitter_cashtags(cashtags=["$AAPL"])
        
        # Verify save was not called (no tweets)
        mock_save.assert_not_called()
        
        # Verify warning was logged
        assert any("No tweets retrieved" in record.message for record in caplog.records)
    
    @patch('src.ingestion.twitter_ingest.sntwitter.TwitterSearchScraper')
    @patch('src.ingestion.twitter_ingest.save_to_parquet')
    def test_handles_tweet_without_date(self, mock_save, mock_scraper_class):
        """Test that tweets without date are handled gracefully."""
        mock_tweet = MagicMock()
        mock_tweet.rawContent = "Test tweet"
        mock_tweet.date = None  # No date
        mock_tweet.likeCount = 5
        mock_tweet.retweetCount = 1
        
        mock_scraper = MagicMock()
        mock_scraper.get_items.return_value = iter([mock_tweet])
        mock_scraper_class.return_value = mock_scraper
        
        ingest_twitter_cashtags(cashtags=["$AAPL"])
        
        saved_df = mock_save.call_args[0][0]
        assert saved_df['created_at'].iloc[0] is None
    
    @patch('src.ingestion.twitter_ingest.sntwitter.TwitterSearchScraper')
    @patch('src.ingestion.twitter_ingest.save_to_parquet')
    def test_handles_tweet_without_engagement_metrics(self, mock_save, mock_scraper_class):
        """Test that tweets without engagement metrics default to 0."""
        mock_tweet = MagicMock()
        mock_tweet.rawContent = "Test tweet"
        mock_tweet.date = datetime(2024, 1, 15, 10, 30)
        # Remove likeCount and retweetCount attributes
        delattr(mock_tweet, 'likeCount')
        delattr(mock_tweet, 'retweetCount')
        
        mock_scraper = MagicMock()
        mock_scraper.get_items.return_value = iter([mock_tweet])
        mock_scraper_class.return_value = mock_scraper
        
        ingest_twitter_cashtags(cashtags=["$AAPL"])
        
        saved_df = mock_save.call_args[0][0]
        assert saved_df['likes'].iloc[0] == 0
        assert saved_df['retweets'].iloc[0] == 0
    
    @patch('src.ingestion.twitter_ingest.sntwitter.TwitterSearchScraper')
    @patch('src.ingestion.twitter_ingest.save_to_parquet')
    def test_logs_start_event(self, mock_save, mock_scraper_class, caplog):
        """Test that start event is logged."""
        mock_tweet = MagicMock()
        mock_tweet.rawContent = "Test tweet"
        mock_tweet.date = datetime(2024, 1, 15, 10, 30)
        mock_tweet.likeCount = 5
        mock_tweet.retweetCount = 1
        
        mock_scraper = MagicMock()
        mock_scraper.get_items.return_value = iter([mock_tweet])
        mock_scraper_class.return_value = mock_scraper
        
        with caplog.at_level(logging.INFO):
            ingest_twitter_cashtags(cashtags=["$AAPL"])
        
        # Verify start event was logged
        assert any("Starting Twitter ingestion" in record.message for record in caplog.records)
    
    @patch('src.ingestion.twitter_ingest.sntwitter.TwitterSearchScraper')
    @patch('src.ingestion.twitter_ingest.save_to_parquet')
    def test_logs_completion_with_row_count(self, mock_save, mock_scraper_class, caplog):
        """Test that completion event is logged with row count."""
        # Create 3 mock tweets
        mock_tweets = []
        for i in range(3):
            mock_tweet = MagicMock()
            mock_tweet.rawContent = f"Tweet {i}"
            mock_tweet.date = datetime(2024, 1, 15, 10, i)
            mock_tweet.likeCount = i
            mock_tweet.retweetCount = i
            mock_tweets.append(mock_tweet)
        
        mock_scraper = MagicMock()
        mock_scraper.get_items.return_value = iter(mock_tweets)
        mock_scraper_class.return_value = mock_scraper
        
        with caplog.at_level(logging.INFO):
            ingest_twitter_cashtags(cashtags=["$AAPL"])
        
        # Verify completion event was logged with row count
        assert any("Completed Twitter ingestion: 3 rows" in record.message for record in caplog.records)
    
    @patch('src.ingestion.twitter_ingest.sntwitter.TwitterSearchScraper')
    @patch('src.ingestion.twitter_ingest.save_to_parquet')
    def test_uses_default_parameters(self, mock_save, mock_scraper_class):
        """Test that default parameters are used when not specified."""
        mock_tweet = MagicMock()
        mock_tweet.rawContent = "Test tweet"
        mock_tweet.date = datetime(2024, 1, 15, 10, 30)
        mock_tweet.likeCount = 5
        mock_tweet.retweetCount = 1
        
        mock_scraper = MagicMock()
        mock_scraper.get_items.return_value = iter([mock_tweet])
        mock_scraper_class.return_value = mock_scraper
        
        # Call without parameters
        ingest_twitter_cashtags()
        
        # Verify default cashtags were used
        assert mock_scraper_class.call_count == 2  # Default: ["$AAPL", "$TSLA"]
        
        # Verify both default cashtags were called
        calls = [call[0][0] for call in mock_scraper_class.call_args_list]
        assert "$AAPL" in calls
        assert "$TSLA" in calls
