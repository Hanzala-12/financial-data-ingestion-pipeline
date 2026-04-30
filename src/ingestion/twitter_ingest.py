"""
Twitter/X data ingestion module.

This module scrapes tweets containing financial cashtags using snscrape
and saves them to Parquet format with metadata columns.
"""

import os
from datetime import datetime
from typing import List
import pandas as pd
import snscrape.modules.twitter as sntwitter

from .utils import setup_logging, get_timestamp_filename, save_to_parquet


def ingest_twitter_cashtags(
    cashtags: List[str] = ["$AAPL", "$TSLA"],
    limit: int = 100
) -> None:
    """
    Ingest tweets containing specified cashtags.
    
    For each cashtag, scrapes tweets and saves them to a Parquet file
    with added metadata columns (cashtag and ingestion timestamp).
    
    Args:
        cashtags: List of cashtags (default: ["$AAPL", "$TSLA"])
        limit: Maximum tweets per cashtag (default: 100)
    
    Raises:
        Exception: Logs error and continues if individual cashtag fails
    """
    logger = setup_logging("twitter_ingest")
    logger.info(f"Starting Twitter ingestion for cashtags: {cashtags}")
    
    all_tweets = []
    
    for cashtag in cashtags:
        try:
            logger.info(f"Scraping tweets for {cashtag}")
            
            # Scrape tweets using snscrape
            tweets = []
            scraper = sntwitter.TwitterSearchScraper(cashtag)
            
            for i, tweet in enumerate(scraper.get_items()):
                if i >= limit:
                    break
                
                tweets.append({
                    'text': tweet.rawContent,
                    'created_at': tweet.date.isoformat() if tweet.date else None,
                    'likes': tweet.likeCount if hasattr(tweet, 'likeCount') else 0,
                    'retweets': tweet.retweetCount if hasattr(tweet, 'retweetCount') else 0,
                    'cashtag': cashtag
                })
            
            if not tweets:
                logger.warning(f"No tweets retrieved for {cashtag}")
                continue
            
            logger.info(f"Retrieved {len(tweets)} tweets for {cashtag}")
            all_tweets.extend(tweets)
            
        except Exception as e:
            logger.error(f"Failed to scrape tweets for {cashtag}: {e}", exc_info=True)
            continue
    
    # Save all tweets to a single file
    if all_tweets:
        try:
            # Create DataFrame
            df = pd.DataFrame(all_tweets)
            
            # Add ingestion timestamp
            df['ingested_at'] = datetime.now().isoformat()
            
            # Generate output path
            filename = get_timestamp_filename("twitter")
            output_path = os.path.join("data", "raw", "twitter", filename)
            
            # Save to Parquet
            save_to_parquet(df, output_path)
            
            logger.info(f"Completed Twitter ingestion: {len(df)} rows")
            
        except Exception as e:
            logger.error(f"Failed to save Twitter data: {e}", exc_info=True)
            raise
    else:
        logger.warning("No tweets retrieved from any cashtag")


if __name__ == "__main__":
    ingest_twitter_cashtags()
