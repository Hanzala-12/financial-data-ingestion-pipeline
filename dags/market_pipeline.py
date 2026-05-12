"""Airflow DAG for the market prediction pipeline.

THIS IS THE AUTHORITATIVE DAG FOR THE MARKET PREDICTION PIPELINE.

Do NOT use the DAG from airflow/dags/ - it is legacy and has been deprecated.
See airflow/dags/market_prediction_pipeline.py for migration notes.

This DAG orchestrates the complete ML pipeline:
  1. Ingest: Collect price and news data from multiple sources
  2. Sentiment: Classify and aggregate sentiment from ingested data
  3. Features: Build feature frame with technical indicators for model training
  4. Train: Train all sequential models (direction, trend, volatility)

The DAG is scheduled to run hourly at the top of each hour via cron: "0 * * * *"
"""

from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import sys

from airflow import DAG
from airflow.operators.python import PythonOperator

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.run_all import run_pipeline
from src.sentiment.processor import run_sentiment_pipeline
from src.market_direction.build_features import build_feature_frame


def ingest_all() -> None:
    """Run the ingestion pipeline once and exit."""
    run_pipeline()



def run_sentiment() -> None:
    """Run sentiment labeling and hourly aggregation."""
    run_sentiment_pipeline()



def build_features() -> None:
    """Build and persist the merged feature frame."""
    build_feature_frame(add_technical_indicators=True)



def train_models() -> None:
    """Train the sequential models using the training entrypoint."""
    subprocess.run(
        [sys.executable, "-m", "src.train.train_models"],
        check=True,
        cwd=str(PROJECT_ROOT),
    )



default_args = {
    "owner": "mlops",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="market_prediction_pipeline",
    default_args=default_args,
    description="Ingest -> sentiment -> features -> train",
    schedule="0 * * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["market", "mlops", "production"],
) as dag:
    ingest_task = PythonOperator(task_id="ingest_all", python_callable=ingest_all)
    sentiment_task = PythonOperator(task_id="run_sentiment", python_callable=run_sentiment)
    features_task = PythonOperator(task_id="build_features", python_callable=build_features)
    train_task = PythonOperator(task_id="train_models", python_callable=train_models)

    ingest_task >> sentiment_task >> features_task >> train_task
