"""
Reuters RSS feed ingestion module.

This module retrieves business news articles from Reuters RSS feed
and saves them to Parquet format with metadata columns.
"""

import os
from datetime import datetime
import pandas as pd
import feedparser

from .utils import setup_logging, get_timestamp_filename, save_to_parquet


def ingest_reuters_feed(
    feed_url: str = "http://feeds.reuters.com/reuters/businessNews"
) -> bool:
    """
    Ingest articles from Reuters RSS feed.
    
    Parses the RSS feed, extracts article metadata (title, link, published_date),
    and saves it to a Parquet file with an added ingestion timestamp.
    
    Args:
        feed_url: RSS feed URL (default: Reuters business news)
    
    Returns:
        bool: True if ingestion succeeded, False if feed unavailable
    
    Raises:
        Exception: Logs error and returns False if feed unavailable
    """
    logger = setup_logging("reuters_ingest")
    logger.info(f"Starting Reuters RSS feed ingestion from {feed_url}")
    
    try:
        # Parse RSS feed
        logger.info("Fetching RSS feed")
        feed = feedparser.parse(feed_url)
        
        # Check if feed was successfully retrieved
        if feed.bozo:
            logger.error(f"Feed parsing error: {feed.bozo_exception}")
            return False
        
        if not feed.entries:
            logger.warning("No entries found in RSS feed")
            return False
        
        # Extract article data
        articles = []
        for entry in feed.entries:
            article = {
                'title': entry.get('title', ''),
                'link': entry.get('link', ''),
                'published_date': entry.get('published', '')
            }
            articles.append(article)
        
        # Create DataFrame
        df = pd.DataFrame(articles)
        
        # Add metadata column
        df['ingested_at'] = datetime.now().isoformat()
        
        # Generate output path
        filename = get_timestamp_filename("reuters")
        output_path = os.path.join("data", "raw", "reuters", filename)
        
        # Save to Parquet
        save_to_parquet(df, output_path)
        
        logger.info(f"Completed Reuters ingestion: {len(df)} rows")
        return True
        
    except Exception as e:
        logger.error(f"Failed to ingest Reuters feed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    ingest_reuters_feed()
