"""Entry point for training market direction models."""

from pathlib import Path
import argparse

import mlflow

from .pipeline import (
    DEFAULT_PRICE_DIR,
    DEFAULT_SENTIMENT_PATH,
    FEATURE_COLUMNS,
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

    print("="*60)
    print("ENHANCED TRAINING PIPELINE")
    print("="*60)
    print(f"Window size: {args.window}")
    print(f"Batch size: {args.batch_size}")
    print(f"Epochs: {args.epochs}")
    print(f"Learning rate: {args.learning_rate}")
    print("="*60)

    print("\n[1/6] Loading price data...")
    price_df = load_price_data(args.price_dir)
    print(f"✓ Loaded {len(price_df)} price records")
    
    print("\n[2/6] Loading sentiment data...")
    sentiment_ts = load_sentiment_data(args.sentiment_path)
    print(f"✓ Loaded {len(sentiment_ts)} sentiment records")
    
    print("\n[3/6] Preparing features with technical indicators...")
    feature_frame = prepare_feature_frame(
        price_df,
        sentiment_ts,
        missing_strategy=args.missing_strategy,
        add_technical_indicators=True,
    )
    print(f"✓ Feature frame shape: {feature_frame.shape}")
    print(f"✓ Total features: {len(FEATURE_COLUMNS)}")

    print("\n[4/6] Building sliding windows...")
    features, labels, scaler = build_sliding_windows(
        feature_frame,
        window_size=args.window,
        normalize=True,
    )
    if len(features) == 0:
        raise ValueError("No sliding window samples were generated")
    
    print(f"✓ Original samples: {len(features)}")
    print(f"✓ Feature shape: {features.shape}")
    
    # Generate synthetic data if we have less than 5000 samples
    if len(features) < 5000:
        print("\n[5/6] Generating synthetic data...")
        from src.features.synthetic_data import generate_synthetic_data
        
        features, labels = generate_synthetic_data(
            features,
            labels,
            target_size=10000,
            methods=['noise', 'time_warp', 'window_slice', 'magnitude_scale']
        )
        print(f"✓ Total samples after augmentation: {len(features)}")
    else:
        print(f"\n[5/6] Skipping synthetic data generation (have {len(features)} samples)")

    print("\n[6/6] Splitting dataset and creating dataloaders...")
    train, val, test = split_dataset(features, labels)
    loaders = create_dataloaders(
        train,
        val,
        test,
        batch_size=args.batch_size,
    )
    print(f"✓ Train: {len(train[0])}, Val: {len(val[0])}, Test: {len(test[0])}")

    if not args.disable_mlflow:
        mlflow.set_experiment(args.experiment_name)

    config = TrainingConfig(
        window_size=args.window,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        epochs=args.epochs,
        patience=args.patience,
    )

    print("\n" + "="*60)
    print("STARTING MODEL TRAINING")
    print("="*60)
    
    results = run_all_models(
        loaders,
        config,
        model_dir=args.model_dir,
        artifact_dir=args.artifact_dir,
        mlflow_enabled=not args.disable_mlflow,
    )

    print("\n" + "="*60)
    print("TRAINING COMPLETE - FINAL RESULTS")
    print("="*60)
    print(format_comparison_table(results))
    print("="*60)


if __name__ == "__main__":
    main()
