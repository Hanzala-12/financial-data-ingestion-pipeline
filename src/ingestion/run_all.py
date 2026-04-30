"""
Pipeline orchestrator for financial data ingestion.

This module executes all ingestion components in sequence with comprehensive
error handling and logging. Individual ingestor failures are isolated to prevent
cascading failures.
"""

from datetime import datetime
from typing import Dict

from .utils import setup_logging
from .yahoo_ingest import ingest_yahoo_data
from .reuters_ingest import ingest_reuters_feed
from .reddit_ingest import ingest_reddit_posts
from .twitter_ingest import ingest_twitter_cashtags


def run_pipeline() -> Dict[str, bool]:
    """
    Execute all ingestion components.
    
    Runs all ingestors in sequence: Yahoo Finance, Reuters RSS, Reddit, and Twitter.
    Each ingestor is wrapped in error handling to isolate failures and allow the
    pipeline to continue processing remaining sources.
    
    Returns:
        Dictionary mapping ingestor name to success status (True/False)
    """
    logger = setup_logging("pipeline_orchestrator")
    
    # Log pipeline start time
    start_time = datetime.now()
    logger.info(f"Pipeline started at {start_time.isoformat()}")
    
    # Track results for each ingestor
    results = {}
    
    # Execute Yahoo Finance ingestor
    try:
        logger.info("Executing Yahoo Finance ingestor")
        ingest_yahoo_data()
        results['yahoo'] = True
        logger.info("Yahoo Finance ingestor completed successfully")
    except Exception as e:
        results['yahoo'] = False
        logger.error(f"Yahoo Finance ingestor failed: {e}", exc_info=True)
    
    # Execute Reuters RSS ingestor
    try:
        logger.info("Executing Reuters RSS ingestor")
        success = ingest_reuters_feed()
        results['reuters'] = success
        if success:
            logger.info("Reuters RSS ingestor completed successfully")
        else:
            logger.error("Reuters RSS ingestor failed")
    except Exception as e:
        results['reuters'] = False
        logger.error(f"Reuters RSS ingestor failed: {e}", exc_info=True)
    
    # Execute Reddit ingestor
    try:
        logger.info("Executing Reddit ingestor")
        success = ingest_reddit_posts()
        results['reddit'] = success
        if success:
            logger.info("Reddit ingestor completed successfully")
        else:
            logger.error("Reddit ingestor failed")
    except Exception as e:
        results['reddit'] = False
        logger.error(f"Reddit ingestor failed: {e}", exc_info=True)
    
    # Execute Twitter ingestor
    try:
        logger.info("Executing Twitter ingestor")
        ingest_twitter_cashtags()
        results['twitter'] = True
        logger.info("Twitter ingestor completed successfully")
    except Exception as e:
        results['twitter'] = False
        logger.error(f"Twitter ingestor failed: {e}", exc_info=True)
    
    # Log pipeline end time and summary
    end_time = datetime.now()
    logger.info(f"Pipeline ended at {end_time.isoformat()}")
    
    # Calculate success count
    success_count = sum(1 for status in results.values() if status)
    total_count = len(results)
    
    logger.info(f"Pipeline summary: {success_count}/{total_count} ingestors successful")
    
    return results


if __name__ == "__main__":
    run_pipeline()
