# Requirements Document

## Introduction

This document specifies the requirements for a production-ready financial data ingestion pipeline designed to collect market data and sentiment signals from multiple sources for machine learning-based financial market prediction. The pipeline ingests hourly OHLCV (Open, High, Low, Close, Volume) data from Yahoo Finance, business news from Reuters RSS feeds, social media sentiment from Reddit communities, and Twitter/X cashtag mentions. All data is stored in Parquet format with DVC version control for reproducibility and idempotent execution for reliability.

## Glossary

- **Pipeline**: The complete financial data ingestion system
- **Yahoo_Ingestor**: Component that retrieves OHLCV data from Yahoo Finance API
- **Reuters_Ingestor**: Component that scrapes Reuters RSS business news feed
- **Reddit_Ingestor**: Component that collects posts from investment-related subreddits
- **Twitter_Ingestor**: Component that scrapes tweets containing financial cashtags
- **Orchestrator**: The run_all.py script that executes all ingestion components
- **OHLCV**: Open, High, Low, Close, Volume - standard financial time series data
- **Parquet**: Columnar storage file format optimized for analytics
- **DVC**: Data Version Control system for tracking data files
- **Idempotent**: Property where re-running an operation produces the same result without side effects
- **Cashtag**: Twitter symbol format for stocks (e.g., $AAPL, $TSLA)

## Requirements

### Requirement 1: Yahoo Finance Data Ingestion

**User Story:** As an ML engineer, I want to ingest hourly OHLCV data from Yahoo Finance for specific tickers, so that I can build time-series features for market prediction models.

#### Acceptance Criteria

1. THE Yahoo_Ingestor SHALL retrieve OHLCV data for tickers ["AAPL", "TSLA", "SPY"]
2. THE Yahoo_Ingestor SHALL retrieve data with 1-hour interval granularity
3. THE Yahoo_Ingestor SHALL retrieve data for the last 60 days from execution time
4. WHEN data is retrieved, THE Yahoo_Ingestor SHALL add a ticker column to identify the symbol
5. WHEN data is retrieved, THE Yahoo_Ingestor SHALL add an ingested_at timestamp in ISO 8601 format
6. THE Yahoo_Ingestor SHALL save data to data/raw/yahoo/{ticker}_{YYYYMMDD_HH}.parquet
7. WHEN the Yahoo_Ingestor is executed multiple times, THE Yahoo_Ingestor SHALL produce consistent results without data duplication (idempotent)
8. IF the Yahoo Finance API returns an error, THEN THE Yahoo_Ingestor SHALL log the error and continue processing remaining tickers
9. THE Yahoo_Ingestor SHALL use the yfinance Python library for data retrieval

### Requirement 2: Reuters RSS Feed Ingestion

**User Story:** As an ML engineer, I want to scrape Reuters business news headlines, so that I can extract sentiment signals and news events for market prediction.

#### Acceptance Criteria

1. THE Reuters_Ingestor SHALL retrieve articles from http://feeds.reuters.com/reuters/businessNews
2. WHEN an article is retrieved, THE Reuters_Ingestor SHALL extract the title field
3. WHEN an article is retrieved, THE Reuters_Ingestor SHALL extract the link field
4. WHEN an article is retrieved, THE Reuters_Ingestor SHALL extract the published_date field
5. WHEN an article is retrieved, THE Reuters_Ingestor SHALL add an ingested_at timestamp in ISO 8601 format
6. THE Reuters_Ingestor SHALL save data to data/raw/reuters/reuters_{YYYYMMDD_HH}.parquet
7. WHEN the Reuters_Ingestor is executed multiple times, THE Reuters_Ingestor SHALL produce consistent results without data duplication (idempotent)
8. IF the RSS feed is unavailable, THEN THE Reuters_Ingestor SHALL log the error and exit gracefully
9. THE Reuters_Ingestor SHALL use the feedparser Python library for RSS parsing

### Requirement 3: Reddit Social Sentiment Ingestion

**User Story:** As an ML engineer, I want to collect posts from investment-focused subreddits, so that I can analyze retail investor sentiment for market prediction.

#### Acceptance Criteria

1. THE Reddit_Ingestor SHALL retrieve the top 100 posts from r/investing
2. THE Reddit_Ingestor SHALL retrieve the top 100 posts from r/stocks
3. THE Reddit_Ingestor SHALL retrieve the top 100 posts from r/wallstreetbets
4. WHEN a post is retrieved, THE Reddit_Ingestor SHALL extract the title field
5. WHEN a post is retrieved, THE Reddit_Ingestor SHALL extract the selftext field
6. WHEN a post is retrieved, THE Reddit_Ingestor SHALL extract the created_utc timestamp
7. WHEN a post is retrieved, THE Reddit_Ingestor SHALL extract the score field
8. WHEN a post is retrieved, THE Reddit_Ingestor SHALL extract the num_comments field
9. WHEN a post is retrieved, THE Reddit_Ingestor SHALL add a subreddit column to identify the source
10. WHEN a post is retrieved, THE Reddit_Ingestor SHALL add an ingested_at timestamp in ISO 8601 format
11. THE Reddit_Ingestor SHALL save data to data/raw/reddit/reddit_{YYYYMMDD_HH}.parquet
12. WHEN the Reddit_Ingestor is executed multiple times, THE Reddit_Ingestor SHALL produce consistent results without data duplication (idempotent)
13. IF Reddit API authentication fails, THEN THE Reddit_Ingestor SHALL log the error and exit gracefully
14. THE Reddit_Ingestor SHALL use the PRAW Python library for Reddit API access
15. THE Reddit_Ingestor SHALL load Reddit API credentials from environment variables

### Requirement 4: Twitter/X Cashtag Ingestion

**User Story:** As an ML engineer, I want to scrape tweets containing stock cashtags, so that I can analyze real-time social sentiment for specific securities.

#### Acceptance Criteria

1. THE Twitter_Ingestor SHALL retrieve tweets containing the cashtag $AAPL
2. THE Twitter_Ingestor SHALL retrieve tweets containing the cashtag $TSLA
3. WHEN a tweet is retrieved, THE Twitter_Ingestor SHALL extract the tweet text
4. WHEN a tweet is retrieved, THE Twitter_Ingestor SHALL extract the created_at timestamp
5. WHEN a tweet is retrieved, THE Twitter_Ingestor SHALL extract engagement metrics (likes, retweets)
6. WHEN a tweet is retrieved, THE Twitter_Ingestor SHALL add a cashtag column to identify the search term
7. WHEN a tweet is retrieved, THE Twitter_Ingestor SHALL add an ingested_at timestamp in ISO 8601 format
8. THE Twitter_Ingestor SHALL save data to data/raw/twitter/twitter_{YYYYMMDD_HH}.parquet
9. WHEN the Twitter_Ingestor is executed multiple times, THE Twitter_Ingestor SHALL produce consistent results without data duplication (idempotent)
10. IF the Twitter scraping fails, THEN THE Twitter_Ingestor SHALL log the error and continue processing remaining cashtags
11. THE Twitter_Ingestor SHALL use the snscrape Python library for tweet scraping

### Requirement 5: Pipeline Orchestration

**User Story:** As an ML engineer, I want to execute all ingestion scripts with a single command, so that I can efficiently collect data from all sources.

#### Acceptance Criteria

1. THE Orchestrator SHALL execute the Yahoo_Ingestor
2. THE Orchestrator SHALL execute the Reuters_Ingestor
3. THE Orchestrator SHALL execute the Reddit_Ingestor
4. THE Orchestrator SHALL execute the Twitter_Ingestor
5. WHEN an ingestor fails, THE Orchestrator SHALL log the failure and continue executing remaining ingestors
6. THE Orchestrator SHALL log the start time of the pipeline execution
7. THE Orchestrator SHALL log the end time of the pipeline execution
8. THE Orchestrator SHALL log a summary of successful and failed ingestion tasks
9. THE Orchestrator SHALL be implemented as src/ingestion/run_all.py

### Requirement 6: Logging and Observability

**User Story:** As an ML engineer, I want comprehensive logging throughout the pipeline, so that I can debug issues and monitor execution.

#### Acceptance Criteria

1. THE Pipeline SHALL use Python's logging module for all log output
2. WHEN an ingestor starts execution, THE Pipeline SHALL log the start event with timestamp
3. WHEN an ingestor completes execution, THE Pipeline SHALL log the completion event with row count
4. WHEN an ingestor encounters an error, THE Pipeline SHALL log the error with full traceback
5. THE Pipeline SHALL log at INFO level for normal operations
6. THE Pipeline SHALL log at ERROR level for failures
7. THE Pipeline SHALL include the component name in each log message
8. THE Pipeline SHALL output logs to stdout

### Requirement 7: Configuration Management

**User Story:** As an ML engineer, I want to manage credentials and configuration through environment variables, so that I can deploy the pipeline securely without hardcoded secrets.

#### Acceptance Criteria

1. THE Pipeline SHALL load configuration from a .env file
2. THE Pipeline SHALL use the python-dotenv library for environment variable loading
3. THE Pipeline SHALL load Reddit API credentials from environment variables (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT)
4. THE Pipeline SHALL load Twitter API credentials from environment variables if required by snscrape
5. IF a required environment variable is missing, THEN THE Pipeline SHALL log an error and exit gracefully
6. THE Pipeline SHALL NOT contain hardcoded credentials in source code

### Requirement 8: Data Storage Format

**User Story:** As an ML engineer, I want all raw data stored in Parquet format, so that I can benefit from compression and fast columnar access for analytics.

#### Acceptance Criteria

1. THE Pipeline SHALL save all raw data files in Parquet format
2. THE Pipeline SHALL NOT save data in CSV format
3. THE Pipeline SHALL use the .parquet file extension for all data files
4. THE Pipeline SHALL preserve data types when writing Parquet files
5. THE Pipeline SHALL use Snappy compression for Parquet files

### Requirement 9: Data Version Control

**User Story:** As an ML engineer, I want to track raw data files with DVC, so that I can version datasets and reproduce experiments.

#### Acceptance Criteria

1. THE Pipeline SHALL store raw data in the data/raw/ directory
2. THE Pipeline SHALL configure DVC to track the data/raw/ directory
3. THE Pipeline SHALL include a dvc.yaml configuration file
4. THE Pipeline SHALL include a .dvc/ directory for DVC metadata
5. THE Pipeline SHALL exclude data/raw/ from Git tracking via .gitignore
6. THE Pipeline SHALL include .dvc files in Git for data versioning

### Requirement 10: Directory Structure

**User Story:** As an ML engineer, I want a well-organized directory structure, so that I can easily navigate the project and understand data flow.

#### Acceptance Criteria

1. THE Pipeline SHALL create a data/raw/yahoo/ directory for Yahoo Finance data
2. THE Pipeline SHALL create a data/raw/reuters/ directory for Reuters RSS data
3. THE Pipeline SHALL create a data/raw/reddit/ directory for Reddit data
4. THE Pipeline SHALL create a data/raw/twitter/ directory for Twitter data
5. THE Pipeline SHALL create a src/ingestion/ directory for ingestion scripts
6. THE Pipeline SHALL organize code into yahoo_ingest.py, reuters_ingest.py, reddit_ingest.py, and twitter_ingest.py modules
7. WHEN a directory does not exist, THE Pipeline SHALL create it automatically before writing data

### Requirement 11: Error Handling and Resilience

**User Story:** As an ML engineer, I want robust error handling in the pipeline, so that transient failures do not cause complete pipeline failure.

#### Acceptance Criteria

1. WHEN a network request fails, THE Pipeline SHALL log the error and continue execution
2. WHEN an API rate limit is encountered, THE Pipeline SHALL log a warning with the rate limit details
3. WHEN a file write operation fails, THE Pipeline SHALL log the error with the file path
4. IF an ingestor encounters an unrecoverable error, THEN THE Pipeline SHALL exit that ingestor gracefully without crashing the entire pipeline
5. THE Pipeline SHALL use try-except blocks around all external API calls
6. THE Pipeline SHALL use try-except blocks around all file I/O operations

### Requirement 12: Idempotency and Data Deduplication

**User Story:** As an ML engineer, I want the pipeline to be idempotent, so that I can safely re-run ingestion without creating duplicate data.

#### Acceptance Criteria

1. WHEN an ingestor is executed multiple times within the same hour, THE Pipeline SHALL overwrite the existing file rather than append
2. THE Pipeline SHALL use timestamp-based filenames to partition data by execution time
3. THE Pipeline SHALL use the format {source}_{YYYYMMDD_HH}.parquet for all output files
4. WHEN data for a specific hour already exists, THE Pipeline SHALL replace it with fresh data
5. THE Pipeline SHALL NOT create duplicate records for the same time period

### Requirement 13: Dependency Management

**User Story:** As an ML engineer, I want clear dependency specifications, so that I can reproduce the environment and deploy the pipeline reliably.

#### Acceptance Criteria

1. THE Pipeline SHALL include a requirements.txt file listing all Python dependencies
2. THE requirements.txt SHALL specify yfinance for Yahoo Finance data
3. THE requirements.txt SHALL specify feedparser for Reuters RSS parsing
4. THE requirements.txt SHALL specify praw for Reddit API access
5. THE requirements.txt SHALL specify snscrape for Twitter scraping
6. THE requirements.txt SHALL specify pandas for data manipulation
7. THE requirements.txt SHALL specify pyarrow for Parquet file operations
8. THE requirements.txt SHALL specify python-dotenv for environment variable management
9. THE requirements.txt SHALL specify dvc for data version control
10. THE requirements.txt SHALL pin major versions to ensure compatibility
