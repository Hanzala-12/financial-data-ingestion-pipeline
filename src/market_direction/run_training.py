"""Entry point for training market direction models."""

from pathlib import Path
import argparse

import mlflow

from .pipeline import (
    DEFAULT_PRICE_DIR,
    DEFAULT_SENTIMENT_PATH,
    TrainingConfig,
    build_sliding_windows,
    create_dataloaders,
    format_comparison_table,
    load_price_data,
    load_sentiment_data,
    prepare_feature_frame,
    run_all_models,
    split_dataset,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train market direction models")
    parser.add_argument(
        "--price-dir",
        type=Path,
        default=DEFAULT_PRICE_DIR,
        help="Directory containing Yahoo parquet files",
    )
    parser.add_argument(
        "--sentiment-path",
        type=Path,
        default=DEFAULT_SENTIMENT_PATH,
        help="Path to sentiment_hourly.parquet",
    )
    parser.add_argument("--window", type=int, default=24, help="Sliding window size")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--patience", type=int, default=5)
    parser.add_argument(
        "--missing-strategy",
        choices=["fill", "drop"],
        default="fill",
        help="How to handle missing values",
    )
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=Path("models"),
        help="Directory to save trained models",
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=Path("artifacts"),
        help="Directory to save evaluation artifacts",
    )
    parser.add_argument(
        "--experiment-name",
        type=str,
        default="market_direction",
        help="MLflow experiment name",
    )
    parser.add_argument(
        "--disable-mlflow",
        action="store_true",
        help="Disable MLflow logging",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    price_df = load_price_data(args.price_dir)
    sentiment_ts = load_sentiment_data(args.sentiment_path)
    feature_frame = prepare_feature_frame(
        price_df,
        sentiment_ts,
        missing_strategy=args.missing_strategy,
    )

    features, labels = build_sliding_windows(
        feature_frame,
        window_size=args.window,
    )
    if len(features) == 0:
        raise ValueError("No sliding window samples were generated")

    train, val, test = split_dataset(features, labels)
    loaders = create_dataloaders(
        train,
        val,
        test,
        batch_size=args.batch_size,
    )

    if not args.disable_mlflow:
        mlflow.set_experiment(args.experiment_name)

    config = TrainingConfig(
        window_size=args.window,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        epochs=args.epochs,
        patience=args.patience,
    )

    results = run_all_models(
        loaders,
        config,
        model_dir=args.model_dir,
        artifact_dir=args.artifact_dir,
        mlflow_enabled=not args.disable_mlflow,
    )

    print(format_comparison_table(results))


if __name__ == "__main__":
    main()
