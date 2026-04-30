"""
Unit tests for the pipeline orchestrator (run_all.py).

Tests verify that the orchestrator executes all ingestors in sequence,
handles errors gracefully, and provides accurate status reporting.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.ingestion.run_all import run_pipeline


class TestRunPipeline:
    """Test suite for the run_pipeline orchestrator function."""
    
    @patch('src.ingestion.run_all.ingest_twitter_cashtags')
    @patch('src.ingestion.run_all.ingest_reddit_posts')
    @patch('src.ingestion.run_all.ingest_reuters_feed')
    @patch('src.ingestion.run_all.ingest_yahoo_data')
    def test_all_ingestors_succeed(self, mock_yahoo, mock_reuters, mock_reddit, mock_twitter):
        """Test that all ingestors are executed when all succeed."""
        # Configure mocks to succeed
        mock_reuters.return_value = True
        mock_reddit.return_value = True
        
        # Execute pipeline
        results = run_pipeline()
        
        # Verify all ingestors were called
        mock_yahoo.assert_called_once()
        mock_reuters.assert_called_once()
        mock_reddit.assert_called_once()
        mock_twitter.assert_called_once()
        
        # Verify all succeeded
        assert results == {
            'yahoo': True,
            'reuters': True,
            'reddit': True,
            'twitter': True
        }
    
    @patch('src.ingestion.run_all.ingest_twitter_cashtags')
    @patch('src.ingestion.run_all.ingest_reddit_posts')
    @patch('src.ingestion.run_all.ingest_reuters_feed')
    @patch('src.ingestion.run_all.ingest_yahoo_data')
    def test_pipeline_continues_after_yahoo_failure(self, mock_yahoo, mock_reuters, mock_reddit, mock_twitter):
        """Test that pipeline continues when Yahoo ingestor fails."""
        # Configure Yahoo to fail
        mock_yahoo.side_effect = Exception("Yahoo API error")
        mock_reuters.return_value = True
        mock_reddit.return_value = True
        
        # Execute pipeline
        results = run_pipeline()
        
        # Verify all ingestors were attempted
        mock_yahoo.assert_called_once()
        mock_reuters.assert_called_once()
        mock_reddit.assert_called_once()
        mock_twitter.assert_called_once()
        
        # Verify Yahoo failed but others succeeded
        assert results['yahoo'] is False
        assert results['reuters'] is True
        assert results['reddit'] is True
        assert results['twitter'] is True
    
    @patch('src.ingestion.run_all.ingest_twitter_cashtags')
    @patch('src.ingestion.run_all.ingest_reddit_posts')
    @patch('src.ingestion.run_all.ingest_reuters_feed')
    @patch('src.ingestion.run_all.ingest_yahoo_data')
    def test_pipeline_continues_after_reuters_failure(self, mock_yahoo, mock_reuters, mock_reddit, mock_twitter):
        """Test that pipeline continues when Reuters ingestor fails."""
        # Configure Reuters to fail
        mock_reuters.return_value = False
        mock_reddit.return_value = True
        
        # Execute pipeline
        results = run_pipeline()
        
        # Verify all ingestors were attempted
        mock_yahoo.assert_called_once()
        mock_reuters.assert_called_once()
        mock_reddit.assert_called_once()
        mock_twitter.assert_called_once()
        
        # Verify Reuters failed but others succeeded
        assert results['yahoo'] is True
        assert results['reuters'] is False
        assert results['reddit'] is True
        assert results['twitter'] is True
    
    @patch('src.ingestion.run_all.ingest_twitter_cashtags')
    @patch('src.ingestion.run_all.ingest_reddit_posts')
    @patch('src.ingestion.run_all.ingest_reuters_feed')
    @patch('src.ingestion.run_all.ingest_yahoo_data')
    def test_pipeline_continues_after_reddit_failure(self, mock_yahoo, mock_reuters, mock_reddit, mock_twitter):
        """Test that pipeline continues when Reddit ingestor fails."""
        # Configure Reddit to fail
        mock_reuters.return_value = True
        mock_reddit.return_value = False
        
        # Execute pipeline
        results = run_pipeline()
        
        # Verify all ingestors were attempted
        mock_yahoo.assert_called_once()
        mock_reuters.assert_called_once()
        mock_reddit.assert_called_once()
        mock_twitter.assert_called_once()
        
        # Verify Reddit failed but others succeeded
        assert results['yahoo'] is True
        assert results['reuters'] is True
        assert results['reddit'] is False
        assert results['twitter'] is True
    
    @patch('src.ingestion.run_all.ingest_twitter_cashtags')
    @patch('src.ingestion.run_all.ingest_reddit_posts')
    @patch('src.ingestion.run_all.ingest_reuters_feed')
    @patch('src.ingestion.run_all.ingest_yahoo_data')
    def test_pipeline_continues_after_twitter_failure(self, mock_yahoo, mock_reuters, mock_reddit, mock_twitter):
        """Test that pipeline continues when Twitter ingestor fails."""
        # Configure Twitter to fail
        mock_reuters.return_value = True
        mock_reddit.return_value = True
        mock_twitter.side_effect = Exception("Twitter scraping error")
        
        # Execute pipeline
        results = run_pipeline()
        
        # Verify all ingestors were attempted
        mock_yahoo.assert_called_once()
        mock_reuters.assert_called_once()
        mock_reddit.assert_called_once()
        mock_twitter.assert_called_once()
        
        # Verify Twitter failed but others succeeded
        assert results['yahoo'] is True
        assert results['reuters'] is True
        assert results['reddit'] is True
        assert results['twitter'] is False
    
    @patch('src.ingestion.run_all.ingest_twitter_cashtags')
    @patch('src.ingestion.run_all.ingest_reddit_posts')
    @patch('src.ingestion.run_all.ingest_reuters_feed')
    @patch('src.ingestion.run_all.ingest_yahoo_data')
    def test_pipeline_handles_multiple_failures(self, mock_yahoo, mock_reuters, mock_reddit, mock_twitter):
        """Test that pipeline handles multiple ingestor failures gracefully."""
        # Configure multiple ingestors to fail
        mock_yahoo.side_effect = Exception("Yahoo API error")
        mock_reuters.return_value = False
        mock_reddit.return_value = True
        mock_twitter.side_effect = Exception("Twitter scraping error")
        
        # Execute pipeline
        results = run_pipeline()
        
        # Verify all ingestors were attempted
        mock_yahoo.assert_called_once()
        mock_reuters.assert_called_once()
        mock_reddit.assert_called_once()
        mock_twitter.assert_called_once()
        
        # Verify correct status for each
        assert results['yahoo'] is False
        assert results['reuters'] is False
        assert results['reddit'] is True
        assert results['twitter'] is False
    
    @patch('src.ingestion.run_all.ingest_twitter_cashtags')
    @patch('src.ingestion.run_all.ingest_reddit_posts')
    @patch('src.ingestion.run_all.ingest_reuters_feed')
    @patch('src.ingestion.run_all.ingest_yahoo_data')
    def test_pipeline_returns_correct_result_structure(self, mock_yahoo, mock_reuters, mock_reddit, mock_twitter):
        """Test that pipeline returns results dictionary with all ingestor keys."""
        # Configure mocks
        mock_reuters.return_value = True
        mock_reddit.return_value = True
        
        # Execute pipeline
        results = run_pipeline()
        
        # Verify result structure
        assert isinstance(results, dict)
        assert set(results.keys()) == {'yahoo', 'reuters', 'reddit', 'twitter'}
        assert all(isinstance(v, bool) for v in results.values())
