# Financial Data Ingestion Pipeline

A production-ready, automated data ingestion pipeline for financial market analysis. This system collects OHLCV market data, business news, and social media sentiment from multiple sources, storing everything in efficient Parquet format with DVC version control for reproducibility.

## 🎯 Features

- **Multi-Source Data Collection**: Automated ingestion from Yahoo Finance, Reuters RSS, Reddit, and Twitter/X
- **Idempotent Execution**: Timestamp-based file naming prevents data duplication
- **Robust Error Handling**: Individual source failures don't cascade; pipeline continues processing
- **Comprehensive Logging**: Detailed execution logs for debugging and monitoring
- **Data Version Control**: DVC integration for reproducible data pipelines
- **Extensive Testing**: 85+ unit and integration tests with 96% code coverage
- **Sentiment Analysis**: Optional sentiment processing pipeline with VADER and FinBERT

## 📋 Prerequisites

- **Python 3.8+**
- **pip** (Python package manager)
- **DVC** (Data Version Control)
- **Git** (for version control)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Hanzala-12/financial-data-ingestion-pipeline.git
cd financial-data-ingestion-pipeline
```

### 2. Set Up Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Credentials

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your credentials:
# - REDDIT_CLIENT_ID
# - REDDIT_CLIENT_SECRET
# - REDDIT_USER_AGENT
```

### 5. Run the Pipeline

```bash
python src/ingestion/run_all.py
```

## 📊 Data Sources

### Yahoo Finance
- **Data**: Hourly OHLCV (Open, High, Low, Close, Volume) data
- **Tickers**: AAPL, TSLA, SPY (configurable)
- **Period**: Last 60 days
- **Authentication**: None required

### Reuters RSS
- **Data**: Business news headlines and links
- **Feed**: http://feeds.reuters.com/reuters/businessNews
- **Authentication**: None required

### Reddit
- **Data**: Top posts from investment subreddits
- **Subreddits**: r/investing, r/stocks, r/wallstreetbets
- **Limit**: 100 posts per subreddit
- **Authentication**: Reddit API credentials required

### Twitter/X
- **Data**: Tweets containing stock cashtags
- **Cashtags**: $AAPL, $TSLA (configurable)
- **Limit**: 100 tweets per cashtag
- **Authentication**: None required (uses snscrape)

## 📁 Project Structure

```
financial-data-ingestion-pipeline/
├── .kiro/
│   └── specs/                    # Specification documents
├── data/
│   └── raw/                      # Raw ingested data (DVC tracked)
│       ├── yahoo/                # Yahoo Finance OHLCV data
│       ├── reuters/              # Reuters news articles
│       ├── reddit/               # Reddit posts
│       └── twitter/              # Twitter cashtag mentions
├── src/
│   ├── ingestion/                # Ingestion modules
│   │   ├── __init__.py
│   │   ├── utils.py              # Shared utilities
│   │   ├── yahoo_ingest.py       # Yahoo Finance ingestor
│   │   ├── reuters_ingest.py     # Reuters RSS ingestor
│   │   ├── reddit_ingest.py      # Reddit ingestor
│   │   ├── twitter_ingest.py     # Twitter ingestor
│   │   └── run_all.py            # Pipeline orchestrator
│   └── sentiment/                # Sentiment analysis (optional)
├── tests/
│   ├── unit/                     # Unit tests (79 tests)
│   └── integration/              # Integration tests (6 tests)
├── .env.example                  # Environment variable template
├── .gitignore                    # Git exclusions
├── dvc.yaml                      # DVC pipeline configuration
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Reddit API Credentials (required for Reddit ingestion)
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=financial-data-pipeline:v1.0 (by /u/yourusername)

# Optional: Sentiment Analysis Configuration
SENTIMENT_VADER_POS_THRESHOLD=0.05
SENTIMENT_VADER_NEG_THRESHOLD=-0.05
SENTIMENT_FINBERT_BATCH_SIZE=32
SENTIMENT_MAX_WORKERS=4
SENTIMENT_LOG_LEVEL=INFO
```

### Obtaining Reddit API Credentials

1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Select "script" as the app type
4. Fill in the required fields
5. Copy the client ID and secret to your `.env` file

## 📈 Usage

### Running Individual Ingestors

```python
# Yahoo Finance
from src.ingestion.yahoo_ingest import ingest_yahoo_data
ingest_yahoo_data(tickers=["AAPL", "TSLA"], interval="1h", period="60d")

# Reuters RSS
from src.ingestion.reuters_ingest import ingest_reuters_feed
ingest_reuters_feed()

# Reddit
from src.ingestion.reddit_ingest import ingest_reddit_posts
ingest_reddit_posts(subreddits=["investing", "stocks"], limit=100)

# Twitter
from src.ingestion.twitter_ingest import ingest_twitter_cashtags
ingest_twitter_cashtags(cashtags=["$AAPL", "$TSLA"], limit=100)
```

### Running the Full Pipeline

```bash
python src/ingestion/run_all.py
```

The orchestrator executes all ingestors sequentially with error isolation. If one source fails, the pipeline continues processing remaining sources.

### Sentiment Analysis (Optional)

```bash
python -c "from src.sentiment.processor import run_sentiment_pipeline; run_sentiment_pipeline()"
```

Output: `data/processed/sentiment_hourly.parquet`

## 🧪 Testing

### Run All Tests

```bash
pytest tests/
```

### Run Unit Tests Only

```bash
pytest tests/unit/
```

### Run Integration Tests Only

```bash
pytest tests/integration/
```

### Run with Coverage Report

```bash
pytest --cov=src/ingestion tests/
```

## 📦 DVC Workflow

### Initialize DVC (already done)

```bash
dvc init
```

### Track Data Directory

```bash
dvc add data/raw/
```

### Pull Data from Remote

```bash
dvc pull
```

### Push Data to Remote

```bash
dvc push
```

### Reproduce Pipeline

```bash
dvc repro
```

## 📊 Data Schemas

### Yahoo Finance (`data/raw/yahoo/{ticker}_{YYYYMMDD_HH}.parquet`)

| Column | Type | Description |
|--------|------|-------------|
| `Date` | datetime64[ns] | Timestamp (index) |
| `Open` | float64 | Opening price |
| `High` | float64 | Highest price |
| `Low` | float64 | Lowest price |
| `Close` | float64 | Closing price |
| `Volume` | int64 | Trading volume |
| `ticker` | string | Stock ticker symbol |
| `ingested_at` | string | ISO 8601 ingestion timestamp |

### Reuters RSS (`data/raw/reuters/reuters_{YYYYMMDD_HH}.parquet`)

| Column | Type | Description |
|--------|------|-------------|
| `title` | string | Article headline |
| `link` | string | URL to full article |
| `published_date` | string | Publication timestamp |
| `ingested_at` | string | ISO 8601 ingestion timestamp |

### Reddit (`data/raw/reddit/reddit_{YYYYMMDD_HH}.parquet`)

| Column | Type | Description |
|--------|------|-------------|
| `title` | string | Post title |
| `selftext` | string | Post body text |
| `created_utc` | int64 | Unix timestamp |
| `score` | int64 | Upvote score |
| `num_comments` | int64 | Comment count |
| `subreddit` | string | Source subreddit |
| `ingested_at` | string | ISO 8601 ingestion timestamp |

### Twitter/X (`data/raw/twitter/twitter_{YYYYMMDD_HH}.parquet`)

| Column | Type | Description |
|--------|------|-------------|
| `text` | string | Tweet content |
| `created_at` | string | Tweet timestamp |
| `likes` | int64 | Like count |
| `retweets` | int64 | Retweet count |
| `cashtag` | string | Search cashtag |
| `ingested_at` | string | ISO 8601 ingestion timestamp |

### Sentiment Output (`data/processed/sentiment_hourly.parquet`)

| Column | Type | Description |
|--------|------|-------------|
| `hour` | datetime | Hour timestamp |
| `ticker` | string | Stock ticker |
| `net_sentiment` | float | Net sentiment score |
| `mean_score` | float | Average sentiment |
| `pos_count` | int | Positive mentions |
| `neg_count` | int | Negative mentions |
| `text_count` | int | Total mentions |

## 🔍 Troubleshooting

### Missing Credentials

**Error**: `Missing required environment variables: ['REDDIT_CLIENT_ID', ...]`

**Solution**: Ensure your `.env` file contains all required Reddit API credentials.

### API Rate Limits

**Error**: `Failed to ingest data for {ticker}: Rate limit exceeded`

**Solution**: 
- Reduce ingestion frequency
- Implement exponential backoff (future enhancement)
- Use smaller data samples during development

### Feed Unavailable

**Error**: `Feed parsing error: Feed unavailable`

**Solution**: 
- Check internet connectivity
- Verify the RSS feed URL is accessible
- Try again later (feed may be temporarily down)

### Empty Data Retrieved

**Warning**: `No data retrieved for {ticker}`

**Solution**:
- Verify ticker symbol is valid
- Check if market is open (for real-time data)
- Increase the period parameter

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'src'`

**Solution**:
```bash
# Ensure you're in the project root directory
cd financial-data-ingestion-pipeline

# Reinstall dependencies
pip install -r requirements.txt
```

## 🛠️ Development

### Code Style

This project follows PEP 8 style guidelines. All code includes:
- Comprehensive docstrings
- Type hints where applicable
- Descriptive variable names
- Consistent error handling patterns

### Adding a New Data Source

1. Create a new ingestor module in `src/ingestion/`
2. Follow the existing pattern:
   - Use `setup_logging()` for logging
   - Use `get_timestamp_filename()` for file naming
   - Use `save_to_parquet()` for data persistence
   - Implement comprehensive error handling
3. Add unit tests in `tests/unit/`
4. Add integration tests in `tests/integration/`
5. Update `run_all.py` to include the new ingestor
6. Update this README with the new data source

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

For questions or support, please open an issue on GitHub.

## 🙏 Acknowledgments

- **yfinance**: Yahoo Finance API wrapper
- **feedparser**: RSS feed parsing
- **PRAW**: Python Reddit API Wrapper
- **snscrape**: Twitter scraping without API
- **DVC**: Data Version Control
- **pandas**: Data manipulation
- **pyarrow**: Parquet file format support

---

**Built with ❤️ for financial data analysis**
