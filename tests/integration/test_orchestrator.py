"""
Integration tests for the pipeline orchestrator (run_all.py).

These tests execute the full pipeline with real API calls to verify
end-to-end orchestration functionality.
"""

import os
import shutil
import tempfile
import pytest

from src.ingestion.run_all import run_pipeline


class TestOrchestratorIntegration:
    """Integration tests for the pipeline orchestrator."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up test environment and clean up after each test."""
        # Store original directory
        self.original_cwd = os.getcwd()
        
        # Create temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        self.test_data_dir = os.path.join(self.test_dir, "data", "raw")
        os.makedirs(os.path.join(self.test_data_dir, "yahoo"), exist_ok=True)
        os.makedirs(os.path.join(self.test_data_dir, "reuters"), exist_ok=True)
        os.makedirs(os.path.join(self.test_data_dir, "reddit"), exist_ok=True)
        os.makedirs(os.path.join(self.test_data_dir, "twitter"), exist_ok=True)
        
        # Change to test directory
        os.chdir(self.test_dir)
        
        yield
        
        # Clean up: change back to original directory and remove test directory
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_run_pipeline_with_all_ingestors(self):
        """
        Test that run_pipeline() executes all ingestors and returns results.
        
        Validates Requirements 5.1-5.9:
        - Executes all four ingestors (Yahoo, Reuters, Reddit, Twitter)
        - Returns results dictionary with all ingestor names
        - At least one ingestor succeeds (validates pipeline execution)
        - Pipeline continues even if some ingestors fail
        """
        # Execute the full pipeline
        results = run_pipeline()
        
        # Verify results dictionary contains all ingestor names
        assert isinstance(results, dict), "Results should be a dictionary"
        assert 'yahoo' in results, "Results should contain 'yahoo' key"
        assert 'reuters' in results, "Results should contain 'reuters' key"
        assert 'reddit' in results, "Results should contain 'reddit' key"
        assert 'twitter' in results, "Results should contain 'twitter' key"
        
        # Verify all values are boolean
        assert all(isinstance(v, bool) for v in results.values()), \
            "All result values should be boolean"
        
        # Verify at least one ingestor succeeds (to validate pipeline execution)
        # Note: Some ingestors may fail due to missing credentials or API issues,
        # but at least one should succeed (typically Yahoo, which doesn't need auth)
        success_count = sum(1 for status in results.values() if status)
        assert success_count >= 1, \
            f"At least one ingestor should succeed, but got {success_count} successes. Results: {results}"
