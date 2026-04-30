# Financial Data Ingestion Pipeline

## Overview
This project is a scalable, automated data ingestion pipeline designed to retrieve, standardize, and store financial data from multiple sources. It captures OHLCV market data, news articles, and social media sentiment to build a comprehensive raw dataset for quantitative analysis.

## Prerequisites
- Python 3.8+
- pip
- DVC (Data Version Control)

## Setup
1. Clone the repository
2. Create and activate a python virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and fill in the required credentials.

## Usage
To run the full pipeline to ingest data from all sources:
```bash
python src/ingestion/run_all.py
```

## DVC Workflow
- To fetch tracked data: `dvc pull`
- To track new data or changes: `dvc add data/raw` then `dvc push` to remote (if configured)

## Testing
- Run all tests: `pytest tests/`
- Run only unit tests: `pytest tests/unit/`

## Troubleshooting
- **Missing credentials:** Check that `.env` contains valid keys and secrets.
- **API rate limits:** Some sources like Reddit or Yahoo might rate limit if run too frequently.
- **Feed unavailable:** Reuters RSS feed might fail or parse differently.

## Data Schemas
### Yahoo
- `ticker`: string
- `Date`: datetime
- `Open`, `High`, `Low`, `Close`, `Volume`: float/int
- `ingested_at`: ISO 8601 string

### Reuters
- `title`: string
- `link`: string
- `published_date`: string
- `ingested_at`: ISO 8601 string

### Reddit
- `title`: string
- `selftext`: string
- `created_utc`: float
- `score`: int
- `num_comments`: int
- `subreddit`: string
- `ingested_at`: ISO 8601 string

### Twitter/X
- `text`: string
- `created_at`: string
- `likes`: int
- `retweets`: int
- `cashtag`: string
- `ingested_at`: ISO 8601 string