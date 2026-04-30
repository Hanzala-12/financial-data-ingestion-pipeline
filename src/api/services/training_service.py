"""Training trigger service for the API."""

from pathlib import Path
from typing import Optional

import mlflow

from src.market_direction.pipeline import (
    DEFAULT_PRICE_DIR,
    DEFAULT_SENTIMENT_PATH,
    TrainingConfig,
    build_sliding_windows,
    create_dataloaders,
    load_price_data,
    load_sentiment_data,
    prepare_feature_frame,
    run_all_models,
    split_dataset,
)


def retrain_models(
    config: Optional[TrainingConfig] = None,
    price_dir: Path = DEFAULT_PRICE_DIR,
    sentiment_path: Path = DEFAULT_SENTIMENT_PATH,
    model_dir: Path = Path("models"),
    artifact_dir: Path = Path("artifacts"),
) -> None:
    """Run model retraining with the latest data."""
    mlflow.set_experiment("market_direction")
    config = config or TrainingConfig()

    price_df = load_price_data(price_dir)
    sentiment_ts = load_sentiment_data(sentiment_path)
    feature_frame = prepare_feature_frame(
        price_df,
        sentiment_ts,
        missing_strategy="fill",
    )

    features, labels = build_sliding_windows(
        feature_frame,
        window_size=config.window_size,
    )
    if len(features) == 0:
        raise ValueError("No sliding window samples were generated")

    train, val, test = split_dataset(features, labels)
    loaders = create_dataloaders(train, val, test, batch_size=config.batch_size)

    run_all_models(
        loaders,
        config,
        model_dir=model_dir,
        artifact_dir=artifact_dir,
        mlflow_enabled=True,
    )
