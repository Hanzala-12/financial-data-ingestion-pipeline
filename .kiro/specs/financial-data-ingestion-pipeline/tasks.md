# Implementation Plan: Financial Data Ingestion Pipeline

## Overview

This implementation plan breaks down the financial data ingestion pipeline into discrete coding tasks. The pipeline will be built incrementally, starting with project structure and shared utilities, then implementing each ingestor independently, followed by orchestration and testing. Each task builds on previous work to ensure continuous integration and early validation.

## Tasks

- [x] 1. Set up project structure and dependencies
  - Create directory structure: `src/ingestion/`, `data/raw/{yahoo,reuters,reddit,twitter}/`, `tests/{unit,integration}/`
  - Create `requirements.txt` with pinned dependencies: pandas, pyarrow, yfinance, feedparser, praw, snscrape, python-dotenv, dvc, pytest, pytest-cov, pytest-mock
  - Create `.env.example` template with placeholder credentials for Reddit API (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT)
  - Create `.gitignore` to exclude `.env`, `data/raw/`, `__pycache__/`, `*.pyc`
  - Initialize DVC with `dvc init` configuration
  - Create `src/ingestion/__init__.py` as empty module marker
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 13.1-13.10, 9.1-9.6_

- [x] 2. Implement shared utilities module
  - [x] 2.1 Create `src/ingestion/utils.py` with logging, file operations, and timestamp utilities
    - Implement `setup_logging(component_name: str) -> logging.Logger` to configure logging with format `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
    - Implement `ensure_directory_exists(path: str) -> None` to create directories if missing
    - Implement `get_timestamp_filename(source: str, ticker: str = None) -> str` to generate filenames in format `{source}_{YYYYMMDD_HH}.parquet` or `{ticker}_{YYYYMMDD_HH}.parquet`
    - Implement `save_to_parquet(df: pd.DataFrame, filepath: str) -> None` to write Parquet files with Snappy compression and error handling
    - _Requirements: 6.1-6.8, 8.1-8.5, 10.7, 12.2-12.3_
  
  - [x] 2.2 Write unit tests for utilities module
    - Test `setup_logging` creates logger with correct name and format
    - Test `ensure_directory_exists` creates missing directories
    - Test `get_timestamp_filename` generates correct format with regex validation
    - Test `save_to_parquet` writes valid Parquet files with Snappy compression
    - Test error handling in `save_to_parquet` when write fails
    - _Requirements: 6.1-6.8, 8.1-8.5_

- [x] 3. Implement Yahoo Finance ingestor
  - [x] 3.1 Create `src/ingestion/yahoo_ingest.py` with OHLCV data retrieval
    - Implement `ingest_yahoo_data(tickers: List[str] = ["AAPL", "TSLA", "SPY"], interval: str = "1h", period: str = "60d") -> None`
    - For each ticker: call `yfinance.Ticker(ticker).history(period=period, interval=interval)`
    - Add `ticker` column with symbol string
    - Add `ingested_at` column with ISO 8601 timestamp using `datetime.now().isoformat()`
    - Use `get_timestamp_filename("yahoo", ticker)` for output path
    - Write to `data/raw/yahoo/{ticker}_{YYYYMMDD_HH}.parquet` using `save_to_parquet`
    - Wrap each ticker in try-except to log errors and continue processing remaining tickers
    - Log start event, completion with row count, and any errors
    - _Requirements: 1.1-1.9, 6.2-6.4, 8.1-8.5, 11.1, 11.5_
  
  - [x] 3.2 Write unit tests for Yahoo Finance ingestor
    - Mock `yfinance.Ticker` to return sample OHLCV DataFrame
    - Test `ticker` and `ingested_at` columns are added correctly
    - Test filename format matches `{ticker}_{YYYYMMDD_HH}.parquet`
    - Test error handling continues to next ticker on API failure
    - Test logging includes start, completion with row count, and errors
    - _Requirements: 1.1-1.9, 6.2-6.4_

- [x] 4. Implement Reuters RSS ingestor
  - [x] 4.1 Create `src/ingestion/reuters_ingest.py` with RSS feed parsing
    - Implement `ingest_reuters_feed(feed_url: str = "http://feeds.reuters.com/reuters/businessNews") -> bool`
    - Parse feed using `feedparser.parse(feed_url)`
    - Extract fields: `title`, `link`, `published_date` from each entry
    - Add `ingested_at` column with ISO 8601 timestamp
    - Use `get_timestamp_filename("reuters")` for output path
    - Write to `data/raw/reuters/reuters_{YYYYMMDD_HH}.parquet` using `save_to_parquet`
    - Handle feed unavailable error: log error and return False
    - Log start event, completion with row count, and any errors
    - _Requirements: 2.1-2.9, 6.2-6.4, 8.1-8.5, 11.2, 11.4_
  
  - [x] 4.2 Write unit tests for Reuters RSS ingestor
    - Mock `feedparser.parse` to return sample feed entries
    - Test `title`, `link`, `published_date`, `ingested_at` columns are extracted
    - Test filename format matches `reuters_{YYYYMMDD_HH}.parquet`
    - Test graceful exit when feed is unavailable (returns False)
    - Test logging includes start, completion with row count, and errors
    - _Requirements: 2.1-2.9, 6.2-6.4_

- [x] 5. Implement Reddit ingestor
  - [x] 5.1 Create `src/ingestion/reddit_ingest.py` with PRAW authentication and post retrieval
    - Load environment variables using `load_dotenv()`
    - Validate required variables: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
    - Implement `ingest_reddit_posts(subreddits: List[str] = ["investing", "stocks", "wallstreetbets"], limit: int = 100) -> bool`
    - Authenticate with `praw.Reddit(client_id=..., client_secret=..., user_agent=...)`
    - For each subreddit: retrieve top 100 posts using `reddit.subreddit(name).top(limit=limit)`
    - Extract fields: `title`, `selftext`, `created_utc`, `score`, `num_comments`
    - Add `subreddit` column with subreddit name
    - Add `ingested_at` column with ISO 8601 timestamp
    - Use `get_timestamp_filename("reddit")` for output path
    - Write to `data/raw/reddit/reddit_{YYYYMMDD_HH}.parquet` using `save_to_parquet`
    - Handle authentication failure: log error and return False
    - Log start event, completion with row count, and any errors
    - _Requirements: 3.1-3.15, 6.2-6.4, 7.1-7.6, 8.1-8.5, 11.4_
  
  - [x] 5.2 Write unit tests for Reddit ingestor
    - Mock `praw.Reddit` and subreddit API calls to return sample posts
    - Test all required fields are extracted: `title`, `selftext`, `created_utc`, `score`, `num_comments`, `subreddit`, `ingested_at`
    - Test filename format matches `reddit_{YYYYMMDD_HH}.parquet`
    - Test graceful exit when authentication fails (returns False)
    - Test environment variable validation raises error when missing
    - Test logging includes start, completion with row count, and errors
    - _Requirements: 3.1-3.15, 6.2-6.4, 7.1-7.6_

- [x] 6. Checkpoint - Verify core ingestors work independently
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement Twitter/X ingestor
  - [x] 7.1 Create `src/ingestion/twitter_ingest.py` with snscrape tweet scraping
    - Implement `ingest_twitter_cashtags(cashtags: List[str] = ["$AAPL", "$TSLA"], limit: int = 100) -> None`
    - For each cashtag: scrape tweets using `sntwitter.TwitterSearchScraper(cashtag)`
    - Extract fields: `text`, `created_at`, `likes` (likeCount), `retweets` (retweetCount)
    - Add `cashtag` column with search term
    - Add `ingested_at` column with ISO 8601 timestamp
    - Use `get_timestamp_filename("twitter")` for output path
    - Write to `data/raw/twitter/twitter_{YYYYMMDD_HH}.parquet` using `save_to_parquet`
    - Wrap each cashtag in try-except to log errors and continue processing remaining cashtags
    - Log start event, completion with row count, and any errors
    - _Requirements: 4.1-4.11, 6.2-6.4, 8.1-8.5, 11.1, 11.5_
  
  - [x] 7.2 Write unit tests for Twitter ingestor
    - Mock `sntwitter.TwitterSearchScraper` to return sample tweets
    - Test all required fields are extracted: `text`, `created_at`, `likes`, `retweets`, `cashtag`, `ingested_at`
    - Test filename format matches `twitter_{YYYYMMDD_HH}.parquet`
    - Test error handling continues to next cashtag on scraping failure
    - Test logging includes start, completion with row count, and errors
    - _Requirements: 4.1-4.11, 6.2-6.4_

- [x] 8. Implement pipeline orchestrator
  - [x] 8.1 Create `src/ingestion/run_all.py` with sequential execution and error isolation
    - Implement `run_pipeline() -> Dict[str, bool]` that executes all ingestors
    - Log pipeline start time with ISO 8601 timestamp
    - Execute ingestors in sequence: `ingest_yahoo_data()`, `ingest_reuters_feed()`, `ingest_reddit_posts()`, `ingest_twitter_cashtags()`
    - Wrap each ingestor call in try-except to isolate failures and continue pipeline
    - Track success/failure status for each ingestor in results dictionary
    - Log each ingestor's success/failure status
    - Log pipeline end time and summary: "{success_count}/{total_count} ingestors successful"
    - Add `if __name__ == "__main__":` block to call `run_pipeline()`
    - _Requirements: 5.1-5.9, 6.2-6.4, 6.6-6.8, 11.4_
  
  - [x] 8.2 Write unit tests for pipeline orchestrator
    - Mock all ingestor functions
    - Test all ingestors are called in correct sequence
    - Test pipeline continues when individual ingestor fails
    - Test results dictionary contains all ingestor statuses
    - Test logging includes start time, end time, and summary with counts
    - _Requirements: 5.1-5.9, 6.2-6.4_

- [x] 9. Add integration tests
  - [x] 9.1 Write integration test for Yahoo Finance ingestor
    - Test end-to-end execution with real yfinance API (small sample: period="1d")
    - Verify Parquet file is created in `data/raw/yahoo/`
    - Verify file contains required columns: `ticker`, `ingested_at`
    - Verify data types are preserved in Parquet format
    - _Requirements: 1.1-1.9, 8.1-8.5_
  
  - [x] 9.2 Write integration test for idempotency
    - Run Yahoo ingestor twice within same hour
    - Verify only one file exists per ticker (overwrite behavior)
    - Verify file content is consistent between runs
    - _Requirements: 1.7, 12.1-12.5_
  
  - [x] 9.3 Write integration test for orchestrator
    - Run `run_pipeline()` with all ingestors
    - Verify results dictionary contains all ingestor names
    - Verify at least one ingestor succeeds (to validate pipeline execution)
    - _Requirements: 5.1-5.9_

- [x] 10. Configure DVC tracking
  - [x] 10.1 Create `dvc.yaml` with pipeline stage configuration
    - Define `ingest` stage with command `python src/ingestion/run_all.py`
    - Specify dependencies: `src/ingestion/` directory
    - Specify outputs: `data/raw/` with cache enabled
    - _Requirements: 9.1-9.6_
  
  - [x] 10.2 Add DVC tracking for raw data directory
    - Run `dvc add data/raw/` to create `.dvc` tracking file
    - Update `.gitignore` to exclude `data/raw/` but include `data/raw.dvc`
    - _Requirements: 9.1-9.6_

- [x] 11. Create documentation
  - [x] 11.1 Create `README.md` with setup and usage instructions
    - Add project overview and architecture diagram reference
    - Add prerequisites: Python 3.8+, pip, DVC
    - Add setup instructions: clone repo, create venv, install dependencies, configure `.env`
    - Add usage instructions: run `python src/ingestion/run_all.py`
    - Add DVC workflow: `dvc pull` to fetch data, `dvc push` to upload data
    - Add testing instructions: `pytest tests/` for all tests, `pytest tests/unit/` for unit tests only
    - Add troubleshooting section: common errors (missing credentials, API rate limits)
    - Add data schema documentation for each source (Yahoo, Reuters, Reddit, Twitter)
    - _Requirements: 1.1-13.10 (all requirements for comprehensive documentation)_

- [x] 12. Final checkpoint - Verify complete pipeline
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Unit tests use mocking to isolate external dependencies
- Integration tests validate real API connectivity with small samples
- Idempotency tests verify overwrite behavior for timestamp-based filenames
- All ingestors follow consistent patterns: configuration → retrieval → transformation → persistence → error handling
