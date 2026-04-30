"""
Reddit data ingestion module.

This module retrieves top posts from investment-focused subreddits using the PRAW
library and saves them to Parquet format with metadata columns.
"""

import os
from datetime import datetime
from typing import List
import pandas as pd
import praw
from dotenv import load_dotenv

from .utils import setup_logging, get_timestamp_filename, save_to_parquet


def ingest_reddit_posts(
    subreddits: List[str] = ["investing", "stocks", "wallstreetbets"],
    limit: int = 100
) -> bool:
    """
    Ingest top posts from specified subreddits.
    
    Authenticates with Reddit API using PRAW, retrieves top posts from each
    subreddit, and saves them to a Parquet file with metadata columns.
    
    Args:
        subreddits: List of subreddit names (default: ["investing", "stocks", "wallstreetbets"])
        limit: Number of top posts to retrieve per subreddit (default: 100)
    
    Returns:
        bool: True if ingestion succeeded, False if authentication or critical error occurred
    
    Raises:
        Exception: Logs error and returns False if authentication fails
    """
    logger = setup_logging("reddit_ingest")
    logger.info(f"Starting Reddit ingestion for subreddits: {subreddits}")
    
    # Load environment variables
    load_dotenv()
    
    # Validate required environment variables
    required_vars = ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USER_AGENT"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        return False
    
    try:
        # Authenticate with Reddit API
        reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT")
        )
        
        # Test authentication by accessing user info
        logger.info(f"Authenticated with Reddit as read-only user")
        
    except Exception as e:
        logger.error(f"Reddit authentication failed: {e}", exc_info=True)
        return False
    
    # Collect posts from all subreddits
    all_posts = []
    
    for subreddit_name in subreddits:
        try:
            logger.info(f"Fetching top {limit} posts from r/{subreddit_name}")
            
            # Retrieve top posts from subreddit
            subreddit = reddit.subreddit(subreddit_name)
            posts = subreddit.top(limit=limit)
            
            # Extract post data
            for post in posts:
                post_data = {
                    'title': post.title,
                    'selftext': post.selftext,
                    'created_utc': post.created_utc,
                    'score': post.score,
                    'num_comments': post.num_comments,
                    'subreddit': subreddit_name
                }
                all_posts.append(post_data)
            
            logger.info(f"Retrieved {len(all_posts)} posts from r/{subreddit_name}")
            
        except Exception as e:
            logger.error(f"Failed to fetch posts from r/{subreddit_name}: {e}", exc_info=True)
            continue
    
    # Check if any posts were collected
    if not all_posts:
        logger.warning("No posts were collected from any subreddit")
        return False
    
    # Convert to DataFrame
    df = pd.DataFrame(all_posts)
    
    # Add ingested_at timestamp
    df['ingested_at'] = datetime.now().isoformat()
    
    # Generate output path
    filename = get_timestamp_filename("reddit")
    output_path = os.path.join("data", "raw", "reddit", filename)
    
    # Save to Parquet
    try:
        save_to_parquet(df, output_path)
        logger.info(f"Completed Reddit ingestion: {len(df)} rows")
        return True
    except Exception as e:
        logger.error(f"Failed to save Reddit data: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    ingest_reddit_posts()
