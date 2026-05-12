# Market Predictor MLOps Pipeline

End-to-end semester project for ingesting financial data, classifying sentiment, building aligned time-series features, training sequential models, and serving predictions through FastAPI.

## What is already implemented

The repository already contains working ingestion modules, sentiment processing, a time-series training pipeline, a FastAPI backend, a React frontend, and the core Airflow orchestration logic. This update adds the missing repo-level deliverables: a runnable DVC pipeline, Docker and Compose files, an EC2-friendly GitHub Actions workflow, a FastAPI-hosted static testing page, and an IEEE report template.

## Repository Layout

- `src/ingestion/` existing live ingestion code for Yahoo Finance, Reuters RSS, Reddit, and Twitter/X.
- `src/sentiment/` VADER/FinBERT sentiment classification and hourly aggregation.
- `src/features/` feature engineering helpers and technical indicators.
- `src/market_direction/` sequential model pipeline and training utilities.
- `src/train/` runnable training entrypoint that logs to MLflow.
- `src/api/` FastAPI app, model loading, prediction, retraining, and static manual test page.
- `dags/market_pipeline.py` production Airflow DAG.
- `frontend/` existing React/Vite UI.
- `report/main.tex` IEEE LaTeX template.

## Prerequisites

- Python 3.11 or later
- Git
- Docker and Docker Compose
- DVC
- Access to the required API credentials for Reddit and optional Twitter/X scraping
- AWS credentials if you want to use an S3 DVC remote

## Environment Setup

1. Create and activate the existing virtual environment.
2. Install dependencies.
3. Copy `.env.example` to `.env` and fill in the secrets.

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

### Required API keys

- Reddit: create an app at https://www.reddit.com/prefs/apps and set `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, and `REDDIT_USER_AGENT`.
- Twitter/X: optional; if you use a bearer token, set `TWITTER_BEARER_TOKEN`.
- AWS S3 for DVC: set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_DEFAULT_REGION`.

## Local Run

### 1. Ingest live data

```bash
python -m src.ingestion.run_all
```

### 2. Run sentiment aggregation

```bash
python -m src.sentiment.processor
```

### 3. Build the time-series dataset

```bash
python -m src.features.build_ts_dataset
```

### 4. Train the sequential models

```bash
python -m src.train.train_models
```

The training step fits RNN, LSTM, and GRU models, logs to MLflow, and stores the best checkpoints and artifacts in `models/` and `artifacts/`.

### 5. Start the API

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000/` for the static manual testing page.

### 6. Start the React frontend

```bash
cd frontend
npm install
npm run dev
```

## DVC

This repo includes a runnable `dvc.yaml` with four stages:
- `ingest`
- `sentiment`
- `features`
- `train`

To reproduce the pipeline locally:

```bash
dvc repro
```

If you are using S3 remote storage, configure it with:

```bash
dvc remote add -d storage $env:DVC_REMOTE
dvc remote modify storage access_key_id $env:AWS_ACCESS_KEY_ID
dvc remote modify storage secret_access_key $env:AWS_SECRET_ACCESS_KEY
```

## MLflow

Start the tracking server locally if you want a UI for experiments:

```bash
mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri file:./mlruns --default-artifact-root file:./artifacts
```

Then open `http://localhost:5000`.

## Airflow

The production DAG is defined in `dags/market_pipeline.py`. It runs hourly and executes:

1. ingestion
2. sentiment aggregation
3. feature construction
4. training

A simple local pattern is to point Airflow at the `dags/` directory and install this repository in the Airflow environment.

## Docker

Build the API image:

```bash
docker build -t market-predictor-mlops:latest .
```

Run the API and MLflow services with Compose:

```bash
docker compose up --build
```

Use the `mlops` profile to start the optional MLflow container:

```bash
docker compose --profile mlops up --build
```

## Deployment to AWS EC2

1. Launch an EC2 instance with Ubuntu 22.04 or later.
2. Open inbound ports:
   - `22` for SSH from your IP
   - `8000` for FastAPI
   - `5000` for MLflow if you expose it publicly
3. Install Docker and Docker Compose on the instance.
4. Clone the repository or copy the deployment files to `/opt/market-predictor-mlops`.
5. Set the environment variables in the EC2 shell or an `.env` file.
6. Pull the Docker image published by GitHub Actions and start the stack.

Example commands on EC2:

```bash
cd /opt/market-predictor-mlops
docker login -u <dockerhub-user>
docker pull <dockerhub-user>/market-predictor-mlops:latest
docker compose up -d --remove-orphans
```

## GitHub Actions Secrets

Configure these repository secrets for CI/CD:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `EC2_HOST`
- `EC2_USER`
- `EC2_SSH_KEY`

## API Endpoints

- `GET /health`
- `GET /predict?ticker=AAPL&date=2026-05-09`
- `GET /predict/AAPL`
- `POST /predict` with JSON body `{"ticker": "AAPL", "date": "2026-05-09"}`
- `GET /models`
- `GET /sentiment/{ticker}`
- `POST /sentiment/analyze`
- `POST /retrain`

## Report

Compile the IEEE report from `report/main.tex` in Overleaf or locally with a LaTeX distribution.

```bash
pdflatex report/main.tex
```

## Notes

- The API uses the latest data available under `data/raw/yahoo/` and `data/processed/sentiment_hourly.parquet`.
- If the trained model is unavailable, the API falls back to the local checkpoint in `models/`.
- The static testing page is served directly by FastAPI at `/`.

## Results (latest training run)

The most recent full training run completed on 2026-05-10. Final evaluation metrics (direction prediction) are:

- **RNN**: Accuracy = 0.4830, F1 = 0.0000
- **LSTM**: Accuracy = 0.5166, F1 = 0.6810
- **GRU**: Accuracy = 0.5166, F1 = 0.6803

Model checkpoints and related artifacts are available under:

- `models/` (best checkpoints: `rnn_best.pt`, `lstm_best.pt`, `gru_best.pt`)
- `mlruns/` (MLflow experiment runs and metrics)
- `artifacts/` (final_metrics.json and collected_manifest.txt)

You can inspect the MLflow UI locally with:

```bash
mlflow ui --backend-store-uri file:./mlruns --default-artifact-root file:./artifacts
```

