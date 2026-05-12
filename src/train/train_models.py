"""Train the sequential market direction models and log results to MLflow.

THIS IS THE AUTHORITATIVE TRAINING ENTRYPOINT FOR THE MARKET PREDICTION SYSTEM.

Do NOT use src/market_direction/run_training.py - it is legacy and has been deprecated.
See src/market_direction/run_training.py for migration notes.

This module trains three separate tasks:
  1. Direction classification: Binary classification of market direction (up/down)
  2. Trend regression: Continuous prediction of price movement magnitude
  3. Volatility classification: Binary classification of volatility spikes

All models are trained using sequential architectures (RNN, LSTM, GRU) and
logged to MLflow with metrics, parameters, and model artifacts.

Usage:
  python -m src.train.train_models [--options]

The module is used by:
  - dvc.yaml (DVC pipeline orchestration)
  - dags/market_pipeline.py (Airflow DAG orchestration)
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json
from typing import Optional

import mlflow

from src.market_direction.pipeline import (
    DEFAULT_FALLBACK_CSV_PATH,
    DEFAULT_FALLBACK_SENTIMENT_PATH,
    DEFAULT_PRICE_DIR,
    DEFAULT_SENTIMENT_PATH,
    LSTMModel,
    ModelSpec,
    TrainingConfig,
    build_sliding_windows,
    create_dataloaders,
    format_comparison_table,
    load_price_data,
    load_sentiment_data,
    prepare_feature_frame,
    run_experiment,
    run_all_models,
    split_dataset,
)
from src.market_direction.auxiliary_models import (
    create_regression_dataloaders,
    run_trend_experiment,
)

DEFAULT_MODEL_DIR = Path("models")
DEFAULT_ARTIFACT_DIR = Path("artifacts")
DEFAULT_EXPERIMENT_NAME = "market_direction"


def train_models(
    price_dir: Path = DEFAULT_PRICE_DIR,
    sentiment_path: Path = DEFAULT_SENTIMENT_PATH,
    fallback_sentiment_path: Path = DEFAULT_FALLBACK_SENTIMENT_PATH,
    fallback_csv_path: Path = DEFAULT_FALLBACK_CSV_PATH,
    model_dir: Path = DEFAULT_MODEL_DIR,
    artifact_dir: Path = DEFAULT_ARTIFACT_DIR,
    experiment_name: str = DEFAULT_EXPERIMENT_NAME,
    config: Optional[TrainingConfig] = None,
    missing_strategy: str = "fill",
    add_technical_indicators: bool = True,
    enable_mlflow: bool = True,
) -> list[dict]:
    """Train RNN, LSTM, and GRU models against the latest prepared data."""
    config = config or TrainingConfig()
    if enable_mlflow:
        mlflow.set_experiment(experiment_name)

    price_df = load_price_data(price_dir)
    sentiment_ts = load_sentiment_data(
        sentiment_path,
        fallback_path=fallback_sentiment_path,
        fallback_csv_path=fallback_csv_path,
    )
    feature_frame = prepare_feature_frame(
        price_df,
        sentiment_ts,
        missing_strategy=missing_strategy,
        add_technical_indicators=add_technical_indicators,
    )
    features, labels = build_sliding_windows(
        feature_frame,
        window_size=config.window_size,
    )
    if len(features) == 0:
        raise ValueError("No sliding window samples were generated")

    train, val, test = split_dataset(features, labels)
    loaders = create_dataloaders(train, val, test, batch_size=config.batch_size)

    trend_features, trend_labels = build_sliding_windows(
        feature_frame,
        window_size=config.window_size,
        target_column="trend_target",
    )
    if len(trend_features) == 0:
        raise ValueError("No trend samples were generated")
    trend_train, trend_val, trend_test = split_dataset(trend_features, trend_labels)
    trend_loaders = create_regression_dataloaders(
        trend_train,
        trend_val,
        trend_test,
        batch_size=config.batch_size,
    )

    volatility_features, volatility_labels = build_sliding_windows(
        feature_frame,
        window_size=config.window_size,
        target_column="volatility_target",
    )
    if len(volatility_features) == 0:
        raise ValueError("No volatility samples were generated")
    volatility_train, volatility_val, volatility_test = split_dataset(
        volatility_features,
        volatility_labels,
    )
    volatility_loaders = create_dataloaders(
        volatility_train,
        volatility_val,
        volatility_test,
        batch_size=config.batch_size,
    )

    results = run_all_models(
        loaders,
        config,
        model_dir=model_dir,
        artifact_dir=artifact_dir,
        mlflow_enabled=enable_mlflow,
    )

    if enable_mlflow:
        with mlflow.start_run(run_name="TREND"):
            mlflow.log_param("model", "TREND")
            mlflow.log_param("learning_rate", config.learning_rate)
            mlflow.log_param("window_size", config.window_size)
            mlflow.log_param("batch_size", config.batch_size)
            mlflow.log_param("epochs", config.epochs)
            mlflow.log_param("patience", config.patience)
            trend_result = run_trend_experiment(
                model_name="trend",
                input_size=trend_loaders["train"].dataset.features.shape[-1],
                loaders=trend_loaders,
                learning_rate=config.learning_rate,
                epochs=config.epochs,
                patience=config.patience,
                device=config.device,
                model_dir=model_dir,
                artifact_dir=artifact_dir,
                mlflow_enabled=enable_mlflow,
            )
    else:
        trend_result = run_trend_experiment(
            model_name="trend",
            input_size=trend_loaders["train"].dataset.features.shape[-1],
            loaders=trend_loaders,
            learning_rate=config.learning_rate,
            epochs=config.epochs,
            patience=config.patience,
            device=config.device,
            model_dir=model_dir,
            artifact_dir=artifact_dir,
            mlflow_enabled=enable_mlflow,
        )

    volatility_spec = ModelSpec(
        name="VOLATILITY",
        constructor=lambda input_size: LSTMModel(
            input_size=input_size,
            hidden_size=128,
            num_layers=2,
            dropout=0.2,
        ),
        hidden_size=128,
    )
    if enable_mlflow:
        with mlflow.start_run(run_name="VOLATILITY"):
            mlflow.log_param("model", "VOLATILITY")
            mlflow.log_param("learning_rate", config.learning_rate)
            mlflow.log_param("window_size", config.window_size)
            mlflow.log_param("batch_size", config.batch_size)
            mlflow.log_param("epochs", config.epochs)
            mlflow.log_param("patience", config.patience)
            volatility_result = run_experiment(
                volatility_spec,
                volatility_loaders,
                config,
                model_dir=model_dir,
                artifact_dir=artifact_dir,
                mlflow_enabled=enable_mlflow,
            )
    else:
        volatility_result = run_experiment(
            volatility_spec,
            volatility_loaders,
            config,
            model_dir=model_dir,
            artifact_dir=artifact_dir,
            mlflow_enabled=enable_mlflow,
        )

    summary = {
        "experiment_name": experiment_name,
        "window_size": config.window_size,
        "batch_size": config.batch_size,
        "epochs": config.epochs,
        "learning_rate": config.learning_rate,
        "patience": config.patience,
        "results": results,
        "trend": trend_result,
        "volatility": volatility_result,
    }

    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    summary_path = artifact_dir / "training_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    if enable_mlflow:
        mlflow.log_artifact(str(summary_path))

    print(format_comparison_table(results))
    return results



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the market direction models")
    parser.add_argument("--price-dir", type=Path, default=DEFAULT_PRICE_DIR)
    parser.add_argument("--sentiment-path", type=Path, default=DEFAULT_SENTIMENT_PATH)
    parser.add_argument(
        "--fallback-sentiment-path",
        type=Path,
        default=DEFAULT_FALLBACK_SENTIMENT_PATH,
    )
    parser.add_argument(
        "--fallback-csv-path",
        type=Path,
        default=DEFAULT_FALLBACK_CSV_PATH,
    )
    parser.add_argument("--window", type=int, default=24)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--patience", type=int, default=5)
    parser.add_argument("--missing-strategy", choices=["fill", "drop"], default="fill")
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--experiment-name", type=str, default=DEFAULT_EXPERIMENT_NAME)
    parser.add_argument("--disable-mlflow", action="store_true")
    parser.add_argument("--no-technical-indicators", action="store_true")
    return parser.parse_args()



def main() -> None:
    args = parse_args()
    config = TrainingConfig(
        window_size=args.window,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        epochs=args.epochs,
        patience=args.patience,
    )
    train_models(
        price_dir=args.price_dir,
        sentiment_path=args.sentiment_path,
        fallback_sentiment_path=args.fallback_sentiment_path,
        fallback_csv_path=args.fallback_csv_path,
        model_dir=args.model_dir,
        artifact_dir=args.artifact_dir,
        experiment_name=args.experiment_name,
        config=config,
        missing_strategy=args.missing_strategy,
        add_technical_indicators=not args.no_technical_indicators,
        enable_mlflow=not args.disable_mlflow,
    )


if __name__ == "__main__":
    main()
