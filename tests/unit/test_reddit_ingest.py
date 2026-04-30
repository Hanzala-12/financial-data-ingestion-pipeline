"""
Unit tests for the Reddit data ingestion module.
"""

import logging
import os
from datetime import datetime
from unittest.mock import patch, MagicMock, PropertyMock
import pandas as pd
import pytest

from src.ingestion.reddit_ingest import ingest_reddit_posts


class TestIngestRedditPosts:
    """Tests for ingest_reddit_posts function."""
    
    @patch('src.ingestion.reddit_ingest.praw.Reddit')
    @patch('src.ingestion.reddit_ingest.save_to_parquet')
    @patch.dict(os.environ, {
        'REDDIT_CLIENT_ID': 'test_client_id',
        'REDDIT_CLIENT_SECRET': 'test_client_secret',
        'REDDIT_USER_AGENT': 'test_user_agent'
    })
    def test_ingests_posts_successfully(self, mock_save, mock_reddit_class):
        """Test that ingest_reddit_posts processes posts correctly."""
        # Create mock Reddit instance and posts
        mock_reddit = MagicMock()
        mock_reddit_class.return_value = mock_reddit
        
        # Create mock posts for each subreddit
        mock_post1 = MagicMock()
        mock_post1.title = 'Investment Strategy Discussion'
        mock_post1.selftext = 'What are your thoughts on...'
        mock_post1.created_utc = 1705320000
        mock_post1.score = 150
        mock_post1.num_comments = 45
        
        mock_post2 = MagicMock()
        mock_post2.title = 'Stock Analysis: AAPL'
        mock_post2.selftext = 'Apple stock is showing...'
        mock_post2.created_utc = 1705321000
        mock_post2.score = 200
        mock_post2.num_comments = 60
        
        # Mock subreddit.top() to return posts
        mock_subreddit = MagicMock()
        mock_subreddit.top.return_value = [mock_post1, mock_post2]
        mock_reddit.subreddit.return_value = mock_subreddit
        
        # Run ingestion
        result = ingest_reddit_posts(subreddits=["investing"], limit=100)
        
        # Verify Reddit was instantiated correctly
        mock_reddit_class.assert_called_once_with(
            client_id='test_client_id',
            client_secret='test_client_secret',
            user_agent='test_user_agent'
        )
        
        # Verify subreddit was accessed
        mock_reddit.subreddit.assert_called_with("investing")
        mock_subreddit.top.assert_called_with(limit=100)
        
        # Verify save_to_parquet was called
        assert mock_save.call_count == 1
        
        # Verify the DataFrame passed to save_to_parquet has required columns
        saved_df = mock_save.call_args[0][0]
        assert 'title' in saved_df.columns
        assert 'selftext' in saved_df.columns
        assert 'created_utc' in saved_df.columns
        assert 'score' in saved_df.columns
        assert 'num_comments' in saved_df.columns
        assert 'subreddit' in saved_df.columns
        assert 'ingested_at' in saved_df.columns
        
        # Verify data was extracted correctly
        assert len(saved_df) == 2
        assert saved_df['title'].iloc[0] == 'Investment Strategy Discussion'
        assert saved_df['score'].iloc[0] == 150
        assert saved_df['subreddit'].iloc[0] == 'investing'
        
        # Verify function returns True on success
        assert result is True
    
    @patch('src.ingestion.reddit_ingest.praw.Reddit')
    @patch('src.ingestion.reddit_ingest.save_to_parquet')
    @patch.dict(os.environ, {
        'REDDIT_CLIENT_ID': 'test_client_id',
        'REDDIT_CLIENT_SECRET': 'test_client_secret',
        'REDDIT_USER_AGENT': 'test_user_agent'
    })
    def test_extracts_title_field(self, mock_save, mock_reddit_class):
        """Test that title field is extracted correctly."""
        mock_reddit = MagicMock()
        mock_reddit_class.return_value = mock_reddit
        
        mock_post = MagicMock()
        mock_post.title = 'Breaking: Market Volatility Increases'
        mock_post.selftext = 'Post content'
        mock_post.created_utc = 1705320000
        mock_post.score = 100
        mock_post.num_comments = 20
        
        mock_subreddit = MagicMock()
        mock_subreddit.top.return_value = [mock_post]
        mock_reddit.subreddit.return_value = mock_subreddit
        
        ingest_reddit_posts(subreddits=["investing"], limit=100)
        
        saved_df = mock_save.call_args[0][0]
        assert saved_df['title'].iloc[0] == 'Breaking: Market Volatility Increases'
    
    @patch('src.ingestion.reddit_ingest.praw.Reddit')
    @patch('src.ingestion.reddit_ingest.save_to_parquet')
    @patch.dict(os.environ, {
        'REDDIT_CLIENT_ID': 'test_client_id',
        'REDDIT_CLIENT_SECRET': 'test_client_secret',
        'REDDIT_USER_AGENT': 'test_user_agent'
    })
    def test_extracts_selftext_field(self, mock_save, mock_reddit_class):
        """Test that selftext field is extracted correctly."""
        mock_reddit = MagicMock()
        mock_reddit_class.return_value = mock_reddit
        
        mock_post = MagicMock()
        mock_post.title = 'Post Title'
        mock_post.selftext = 'This is the detailed post content with analysis...'
        mock_post.created_utc = 1705320000
        mock_post.score = 100
        mock_post.num_comments = 20
        
        mock_subreddit = MagicMock()
        mock_subreddit.top.return_value = [mock_post]
        mock_reddit.subreddit.return_value = mock_subreddit
        
        ingest_reddit_posts(subreddits=["stocks"], limit=100)
        
        saved_df = mock_save.call_args[0][0]
        assert saved_df['selftext'].iloc[0] == 'This is the detailed post content with analysis...'
    
    @patch('src.ingestion.reddit_ingest.praw.Reddit')
    @patch('src.ingestion.reddit_ingest.save_to_parquet')
    @patch.dict(os.environ, {
        'REDDIT_CLIENT_ID': 'test_client_id',
        'REDDIT_CLIENT_SECRET': 'test_client_secret',
        'REDDIT_USER_AGENT': 'test_user_agent'
    })
    def test_extracts_created_utc_field(self, mock_save, mock_reddit_class):
        """Test that created_utc field is extracted correctly."""
        mock_reddit = MagicMock()
        mock_reddit_class.return_value = mock_reddit
        
        mock_post = MagicMock()
        mock_post.title = 'Post Title'
        mock_post.selftext = 'Post content'
        mock_post.created_utc = 1705320000
        mock_post.score = 100
        mock_post.num_comments = 20
        
        mock_subreddit = MagicMock()
        mock_subreddit.top.return_value = [mock_post]
        mock_reddit.subreddit.return_value = mock_subreddit
        
        ingest_reddit_posts(subreddits=["wallstreetbets"], limit=100)
        
        saved_df = mock_save.call_args[0][0]
        assert saved_df['created_utc'].iloc[0] == 1705320000
    
    @patch('src.ingestion.reddit_ingest.praw.Reddit')
    @patch('src.ingestion.reddit_ingest.save_to_parquet')
    @patch.dict(os.environ, {
        'REDDIT_CLIENT_ID': 'test_client_id',
        'REDDIT_CLIENT_SECRET': 'test_client_secret',
        'REDDIT_USER_AGENT': 'test_user_agent'
    })
    def test_extracts_score_field(self, mock_save, mock_reddit_class):
        """Test that score field is extracted correctly."""
        mock_reddit = MagicMock()
        mock_reddit_class.return_value = mock_reddit
        
        mock_post = MagicMock()
        mock_post.title = 'Post Title'
        mock_post.selftext = 'Post content'
        mock_post.created_utc = 1705320000
        mock_post.score = 500
        mock_post.num_comments = 20
        
        mock_subreddit = MagicMock()
        mock_subreddit.top.return_value = [mock_post]
        mock_reddit.subreddit.return_value = mock_subreddit
        
        ingest_reddit_posts(subreddits=["investing"], limit=100)
        
        saved_df = mock_save.call_args[0][0]
        assert saved_df['score'].iloc[0] == 500
    
    @patch('src.ingestion.reddit_ingest.praw.Reddit')
    @patch('src.ingestion.reddit_ingest.save_to_parquet')
    @patch.dict(os.environ, {
        'REDDIT_CLIENT_ID': 'test_client_id',
        'REDDIT_CLIENT_SECRET': 'test_client_secret',
        'REDDIT_USER_AGENT': 'test_user_agent'
    })
    def test_extracts_num_comments_field(self, mock_save, mock_reddit_class):
        """Test that num_comments field is extracted correctly."""
        mock_reddit = MagicMock()
        mock_reddit_class.return_value = mock_reddit
        
        mock_post = MagicMock()
        mock_post.title = 'Post Title'
        mock_post.selftext = 'Post content'
        mock_post.created_utc = 1705320000
        mock_post.score = 100
        mock_post.num_comments = 75
        
        mock_subreddit = MagicMock()
        mock_subreddit.top.return_value = [mock_post]
        mock_reddit.subreddit.return_value = mock_subreddit
        
        ingest_reddit_posts(subreddits=["stocks"], limit=100)
        
        saved_df = mock_save.call_args[0][0]
        assert saved_df['num_comments'].iloc[0] == 75
    
    @patch('src.ingestion.reddit_ingest.praw.Reddit')
    @patch('src.ingestion.reddit_ingest.save_to_parquet')
    @patch.dict(os.environ, {
        'REDDIT_CLIENT_ID': 'test_client_id',
        'REDDIT_CLIENT_SECRET': 'test_client_secret',
        'REDDIT_USER_AGENT': 'test_user_agent'
    })
    def test_adds_subreddit_column(self, mock_save, mock_reddit_class):
        """Test that subreddit column is added with correct value."""
        mock_reddit = MagicMock()
        mock_reddit_class.return_value = mock_reddit
        
        mock_post = MagicMock()
        mock_post.title = 'Post Title'
        mock_post.selftext = 'Post content'
        mock_post.created_utc = 1705320000
        mock_post.score = 100
        mock_post.num_comments = 20
        
        mock_subreddit = MagicMock()
        mock_subreddit.top.return_value = [mock_post]
        mock_reddit.subreddit.return_value = mock_subreddit
        
        ingest_reddit_posts(subreddits=["wallstreetbets"], limit=100)
        
        saved_df = mock_save.call_args[0][0]
        assert 'subreddit' in saved_df.columns
        assert saved_df['subreddit'].iloc[0] == 'wallstreetbets'
    
    @patch('src.ingestion.reddit_ingest.praw.Reddit')
    @patch('src.ingestion.reddit_ingest.save_to_parquet')
    @patch.dict(os.environ, {
        'REDDIT_CLIENT_ID': 'test_client_id',
        'REDDIT_CLIENT_SECRET': 'test_client_secret',
        'REDDIT_USER_AGENT': 'test_user_agent'
    })
    def test_adds_ingested_at_column_with_iso8601_format(self, mock_save, mock_reddit_class):
        """Test that ingested_at column is added with ISO 8601 timestamp."""
        mock_reddit = MagicMock()
        mock_reddit_class.return_value = mock_reddit
        
        mock_post = MagicMock()
        mock_post.title = 'Post Title'
        mock_post.selftext = 'Post content'
        mock_post.created_utc = 1705320000
        mock_post.score = 100
        mock_post.num_comments = 20
        
        mock_subreddit = MagicMock()
        mock_subreddit.top.return_value = [mock_post]
        mock_reddit.subreddit.return_value = mock_subreddit
        
        ingest_reddit_posts(subreddits=["investing"], limit=100)
        
        # Verify ingested_at column was added
        saved_df = mock_save.call_args[0][0]
        assert 'ingested_at' in saved_df.columns
        
        # Verify ISO 8601 format (should be parseable)
        timestamp_str = saved_df['ingested_at'].iloc[0]
        parsed_timestamp = datetime.fromisoformat(timestamp_str)
        assert isinstance(parsed_timestamp, datetime)
    
    @patch('src.ingestion.reddit_ingest.praw.Reddit')
    @patch('src.ingestion.reddit_ingest.save_to_parquet')
    @patch.dict(os.environ, {
        'REDDIT_CLIENT_ID': 'test_client_id',
        'REDDIT_CLIENT_SECRET': 'test_client_secret',
        'REDDIT_USER_AGENT': 'test_user_agent'
    })
    def test_uses_correct_output_path(self, mock_save, mock_reddit_class):
        """Test that output path follows the required format."""
        mock_reddit = MagicMock()
        mock_reddit_class.return_value = mock_reddit
        
        mock_post = MagicMock()
        mock_post.title = 'Post Title'
        mock_post.selftext = 'Post content'
        mock_post.created_utc = 1705320000
        mock_post.score = 100
        mock_post.num_comments = 20
        
        mock_subreddit = MagicMock()
        mock_subreddit.top.return_value = [mock_post]
        mock_reddit.subreddit.return_value = mock_subreddit
        
        ingest_reddit_posts(subreddits=["investing"], limit=100)
        
        # Verify output path (normalize for cross-platform compatibility)
        output_path = mock_save.call_args[0][1]
        normalized_path = output_path.replace('\\', '/')
        assert normalized_path.startswith("data/raw/reddit/")
        assert "reddit_" in output_path
        assert output_path.endswith(".parquet")
    
    @patch('src.ingestion.reddit_ingest.praw.Reddit')
    @patch('src.ingestion.reddit_ingest.save_to_parquet')
    @patch.dict(os.environ, {
        'REDDIT_CLIENT_ID': 'test_client_id',
        'REDDIT_CLIENT_SECRET': 'test_client_secret',
        'REDDIT_USER_AGENT': 'test_user_agent'
    })
    def test_processes_multiple_subreddits(self, mock_save, mock_reddit_class):
        """Test that multiple subreddits are processed correctly."""
        mock_reddit = MagicMock()
        mock_reddit_class.return_value = mock_reddit
        
        # Create different posts for different subreddits
        mock_post1 = MagicMock()
        mock_post1.title = 'Investing Post'
        mock_post1.selftext = 'Content 1'
        mock_post1.created_utc = 1705320000
        mock_post1.score = 100
        mock_post1.num_comments = 20
        
        mock_post2 = MagicMock()
        mock_post2.title = 'Stocks Post'
        mock_post2.selftext = 'Content 2'
        mock_post2.created_utc = 1705321000
        mock_post2.score = 150
        mock_post2.num_comments = 30
        
        # Mock different returns for different subreddits
        def mock_subreddit_func(name):
            mock_sub = MagicMock()
            if name == "investing":
                mock_sub.top.return_value = [mock_post1]
            elif name == "stocks":
                mock_sub.top.return_value = [mock_post2]
            return mock_sub
        
        mock_reddit.subreddit.side_effect = mock_subreddit_func
        
        ingest_reddit_posts(subreddits=["investing", "stocks"], limit=100)
        
        # Verify both subreddits were accessed
        assert mock_reddit.subreddit.call_count == 2
        
        # Verify DataFrame contains posts from both subreddits
        saved_df = mock_save.call_args[0][0]
        assert len(saved_df) == 2
        assert 'investing' in saved_df['subreddit'].values
        assert 'stocks' in saved_df['subreddit'].values
    
    @patch('src.ingestion.reddit_ingest.praw.Reddit')
    @patch.dict(os.environ, {
        'REDDIT_CLIENT_ID': 'test_client_id',
        'REDDIT_CLIENT_SECRET': 'test_client_secret',
        'REDDIT_USER_AGENT': 'test_user_agent'
    })
    def test_handles_authentication_failure(self, mock_reddit_class, caplog):
        """Test that authentication failure is handled gracefully."""
        # Simulate authentication failure
        mock_reddit_class.side_effect = Exception("Authentication failed")
        
        with caplog.at_level(logging.ERROR):
            result = ingest_reddit_posts(subreddits=["investing"], limit=100)
        
        # Verify error was logged
        assert any("Reddit authentication failed" in record.message for record in caplog.records)
        
        # Verify function returns False on authentication failure
        assert result is False
    
    @patch('src.ingestion.reddit_ingest.praw.Reddit')
    @patch('src.ingestion.reddit_ingest.save_to_parquet')
    @patch.dict(os.environ, {})
    def test_validates_required_environment_variables(self, mock_save, mock_reddit_class, caplog):
        """Test that missing environment variables are detected."""
        with caplog.at_level(logging.ERROR):
            result = ingest_reddit_posts(subreddits=["investing"], limit=100)
        
        # Verify error was logged about missing variables
        assert any("Missing required environment variables" in record.message for record in caplog.records)
        
        # Verify Reddit was not instantiated
        mock_reddit_class.assert_not_called()
        
        # Verify function returns False
        assert result is False
    
    @patch('src.ingestion.reddit_ingest.praw.Reddit')
    @patch('src.ingestion.reddit_ingest.save_to_parquet')
    @patch.dict(os.environ, {
        'REDDIT_CLIENT_ID': 'test_client_id',
        'REDDIT_CLIENT_SECRET': 'test_client_secret',
        'REDDIT_USER_AGENT': 'test_user_agent'
    })
    def test_handles_subreddit_fetch_error(self, mock_save, mock_reddit_class, caplog):
        """Test that errors fetching from individual subreddits are handled."""
        mock_reddit = MagicMock()
        mock_reddit_class.return_value = mock_reddit
        
        # First subreddit fails, second succeeds
        mock_post = MagicMock()
        mock_post.title = 'Stocks Post'
        mock_post.selftext = 'Content'
        mock_post.created_utc = 1705320000
        mock_post.score = 100
        mock_post.num_comments = 20
        
        def mock_subreddit_func(name):
            if name == "investing":
                raise Exception("Subreddit unavailable")
            mock_sub = MagicMock()
            mock_sub.top.return_value = [mock_post]
            return mock_sub
        
        mock_reddit.subreddit.side_effect = mock_subreddit_func
        
        with caplog.at_level(logging.ERROR):
            result = ingest_reddit_posts(subreddits=["investing", "stocks"], limit=100)
        
        # Verify error was logged for failed subreddit
        assert any("Failed to fetch posts from r/investing" in record.message for record in caplog.records)
        
        # Verify function continues and processes successful subreddit
        saved_df = mock_save.call_args[0][0]
        assert len(saved_df) == 1
        assert saved_df['subreddit'].iloc[0] == 'stocks'
        
        # Verify function returns True (partial success)
        assert result is True
    
    @patch('src.ingestion.reddit_ingest.praw.Reddit')
    @patch('src.ingestion.reddit_ingest.save_to_parquet')
    @patch.dict(os.environ, {
        'REDDIT_CLIENT_ID': 'test_client_id',
        'REDDIT_CLIENT_SECRET': 'test_client_secret',
        'REDDIT_USER_AGENT': 'test_user_agent'
    })
    def test_handles_no_posts_collected(self, mock_save, mock_reddit_class, caplog):
        """Test that case where no posts are collected is handled."""
        mock_reddit = MagicMock()
        mock_reddit_class.return_value = mock_reddit
        
        # Return empty list of posts
        mock_subreddit = MagicMock()
        mock_subreddit.top.return_value = []
        mock_reddit.subreddit.return_value = mock_subreddit
        
        with caplog.at_level(logging.WARNING):
            result = ingest_reddit_posts(subreddits=["investing"], limit=100)
        
        # Verify warning was logged
        assert any("No posts were collected" in record.message for record in caplog.records)
        
        # Verify save was not called
        mock_save.assert_not_called()
        
        # Verify function returns False
        assert result is False
    
    @patch('src.ingestion.reddit_ingest.praw.Reddit')
    @patch('src.ingestion.reddit_ingest.save_to_parquet')
    @patch.dict(os.environ, {
        'REDDIT_CLIENT_ID': 'test_client_id',
        'REDDIT_CLIENT_SECRET': 'test_client_secret',
        'REDDIT_USER_AGENT': 'test_user_agent'
    })
    def test_logs_start_event(self, mock_save, mock_reddit_class, caplog):
        """Test that start event is logged."""
        mock_reddit = MagicMock()
        mock_reddit_class.return_value = mock_reddit
        
        mock_post = MagicMock()
        mock_post.title = 'Post Title'
        mock_post.selftext = 'Post content'
        mock_post.created_utc = 1705320000
        mock_post.score = 100
        mock_post.num_comments = 20
        
        mock_subreddit = MagicMock()
        mock_subreddit.top.return_value = [mock_post]
        mock_reddit.subreddit.return_value = mock_subreddit
        
        with caplog.at_level(logging.INFO):
            ingest_reddit_posts(subreddits=["investing"], limit=100)
        
        # Verify start event was logged
        assert any("Starting Reddit ingestion" in record.message for record in caplog.records)
    
    @patch('src.ingestion.reddit_ingest.praw.Reddit')
    @patch('src.ingestion.reddit_ingest.save_to_parquet')
    @patch.dict(os.environ, {
        'REDDIT_CLIENT_ID': 'test_client_id',
        'REDDIT_CLIENT_SECRET': 'test_client_secret',
        'REDDIT_USER_AGENT': 'test_user_agent'
    })
    def test_logs_completion_with_row_count(self, mock_save, mock_reddit_class, caplog):
        """Test that completion event is logged with row count."""
        mock_reddit = MagicMock()
        mock_reddit_class.return_value = mock_reddit
        
        # Create 3 posts
        posts = []
        for i in range(3):
            mock_post = MagicMock()
            mock_post.title = f'Post {i}'
            mock_post.selftext = f'Content {i}'
            mock_post.created_utc = 1705320000 + i
            mock_post.score = 100 + i
            mock_post.num_comments = 20 + i
            posts.append(mock_post)
        
        mock_subreddit = MagicMock()
        mock_subreddit.top.return_value = posts
        mock_reddit.subreddit.return_value = mock_subreddit
        
        with caplog.at_level(logging.INFO):
            ingest_reddit_posts(subreddits=["investing"], limit=100)
        
        # Verify completion event was logged with row count
        assert any("Completed Reddit ingestion: 3 rows" in record.message for record in caplog.records)
    
    @patch('src.ingestion.reddit_ingest.praw.Reddit')
    @patch('src.ingestion.reddit_ingest.save_to_parquet')
    @patch.dict(os.environ, {
        'REDDIT_CLIENT_ID': 'test_client_id',
        'REDDIT_CLIENT_SECRET': 'test_client_secret',
        'REDDIT_USER_AGENT': 'test_user_agent'
    })
    def test_uses_custom_limit(self, mock_save, mock_reddit_class):
        """Test that custom limit parameter is used."""
        mock_reddit = MagicMock()
        mock_reddit_class.return_value = mock_reddit
        
        mock_post = MagicMock()
        mock_post.title = 'Post Title'
        mock_post.selftext = 'Post content'
        mock_post.created_utc = 1705320000
        mock_post.score = 100
        mock_post.num_comments = 20
        
        mock_subreddit = MagicMock()
        mock_subreddit.top.return_value = [mock_post]
        mock_reddit.subreddit.return_value = mock_subreddit
        
        # Use custom limit
        ingest_reddit_posts(subreddits=["investing"], limit=50)
        
        # Verify custom limit was used
        mock_subreddit.top.assert_called_with(limit=50)
    
    @patch('src.ingestion.reddit_ingest.praw.Reddit')
    @patch('src.ingestion.reddit_ingest.save_to_parquet')
    @patch.dict(os.environ, {
        'REDDIT_CLIENT_ID': 'test_client_id',
        'REDDIT_CLIENT_SECRET': 'test_client_secret',
        'REDDIT_USER_AGENT': 'test_user_agent'
    })
    def test_uses_default_subreddits(self, mock_save, mock_reddit_class):
        """Test that default subreddits are used when not specified."""
        mock_reddit = MagicMock()
        mock_reddit_class.return_value = mock_reddit
        
        mock_post = MagicMock()
        mock_post.title = 'Post Title'
        mock_post.selftext = 'Post content'
        mock_post.created_utc = 1705320000
        mock_post.score = 100
        mock_post.num_comments = 20
        
        mock_subreddit = MagicMock()
        mock_subreddit.top.return_value = [mock_post]
        mock_reddit.subreddit.return_value = mock_subreddit
        
        # Call without specifying subreddits
        ingest_reddit_posts()
        
        # Verify default subreddits were used
        assert mock_reddit.subreddit.call_count == 3
        calls = [call[0][0] for call in mock_reddit.subreddit.call_args_list]
        assert "investing" in calls
        assert "stocks" in calls
        assert "wallstreetbets" in calls
