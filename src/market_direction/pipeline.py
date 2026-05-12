"""Binary market direction prediction pipeline."""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple
import copy
import logging
import math

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
import mlflow
import mlflow.pytorch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_PRICE_DIR = DATA_DIR / "raw" / "yahoo"
DEFAULT_SENTIMENT_PATH = DATA_DIR / "processed" / "sentiment_hourly.parquet"
DEFAULT_FALLBACK_SENTIMENT_PATH = DATA_DIR / "processed" / "fallback_sentiment_hourly.parquet"
DEFAULT_FALLBACK_CSV_PATH = DATA_DIR / "fallback_sentiment_aggregated.csv"

FEATURE_COLUMNS = [
    "open",
    "high",
    "low",
    "close",
    "volume",
    "net_sentiment",
    "mean_score",
    "text_count",
    "returns_1h",
    "volatility_6h",
]


@dataclass
class TrainingConfig:
    """Configuration for training."""

    window_size: int = 24
    batch_size: int = 64
    learning_rate: float = 1e-3
    epochs: int = 30
    patience: int = 5
    device: str = "cuda" if torch.cuda.is_available() else "cpu"


@dataclass
class ModelSpec:
    """Specification for a model run."""

    name: str
    constructor: Callable[[int], nn.Module]
    hidden_size: int


class TimeSeriesDataset(Dataset):
    """Dataset wrapper for time-series windows."""

    def __init__(self, features: np.ndarray, labels: np.ndarray) -> None:
        self.features = torch.tensor(features, dtype=torch.float32)
        self.labels = torch.tensor(labels, dtype=torch.float32)

    def __len__(self) -> int:
        return len(self.features)

    def __getitem__(self, index: int) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.features[index], self.labels[index]


class RNNModel(nn.Module):
    """Vanilla RNN classifier."""

    def __init__(
        self,
        input_size: int,
        hidden_size: int = 64,
        num_layers: int = 2,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.rnn = nn.RNN(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            batch_first=True,
        )
        self.fc = nn.Linear(hidden_size, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        output, _ = self.rnn(inputs)
        output = output[:, -1, :]
        return self.sigmoid(self.fc(output))


class LSTMModel(nn.Module):
    """LSTM classifier."""

    def __init__(
        self,
        input_size: int,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            batch_first=True,
        )
        self.fc = nn.Linear(hidden_size, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        output, _ = self.lstm(inputs)
        output = output[:, -1, :]
        return self.sigmoid(self.fc(output))


class GRUModel(nn.Module):
    """GRU classifier."""

    def __init__(
        self,
        input_size: int,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        self.gru = nn.GRU(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            batch_first=True,
        )
        self.fc = nn.Linear(hidden_size, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        output, _ = self.gru(inputs)
        output = output[:, -1, :]
        return self.sigmoid(self.fc(output))


MODEL_SPECS = [
    ModelSpec(
        name="RNN",
        constructor=lambda input_size: RNNModel(
            input_size=input_size,
            hidden_size=64,
            num_layers=2,
            dropout=0.1,
        ),
        hidden_size=64,
    ),
    ModelSpec(
        name="LSTM",
        constructor=lambda input_size: LSTMModel(
            input_size=input_size,
            hidden_size=128,
            num_layers=2,
            dropout=0.2,
        ),
        hidden_size=128,
    ),
    ModelSpec(
        name="GRU",
        constructor=lambda input_size: GRUModel(
            input_size=input_size,
            hidden_size=128,
            num_layers=2,
            dropout=0.2,
        ),
        hidden_size=128,
    ),
]


def normalize_ticker(value: Optional[str]) -> str:
    """Normalize ticker symbols to uppercase."""
    if value is None:
        return "UNKNOWN"
    ticker = str(value).strip().upper()
    return ticker[1:] if ticker.startswith("$") else ticker or "UNKNOWN"


def _resolve_price_timestamp(df: pd.DataFrame, working: pd.DataFrame) -> pd.Series:
    for col in ("datetime", "date", "timestamp", "index"):
        if col in working.columns:
            return pd.to_datetime(working[col], errors="coerce")
    if isinstance(df.index, pd.DatetimeIndex):
        return pd.to_datetime(df.index, errors="coerce")
    raise ValueError("Unable to resolve timestamp column in price data")


def _to_naive_hour(values: pd.Series) -> pd.Series:
    """Convert timestamp-like values to timezone-naive hourly buckets."""
    return pd.to_datetime(values, errors="coerce", utc=True).dt.tz_convert(None).dt.floor(
        "H"
    )


def load_price_data(price_dir: Path = DEFAULT_PRICE_DIR) -> pd.DataFrame:
    """Load Yahoo price data from parquet files."""
    price_dir = Path(price_dir)
    file_paths = sorted(price_dir.rglob("*.parquet"))
    if not file_paths:
        raise FileNotFoundError(f"No parquet files found under {price_dir}")

    frames: List[pd.DataFrame] = []
    for file_path in file_paths:
        df = pd.read_parquet(file_path)
        if df.empty:
            continue

        working = df.copy()
        working.columns = [str(col).lower() for col in working.columns]
        timestamp = _resolve_price_timestamp(df, working)
        if isinstance(timestamp, pd.DatetimeIndex):
            timestamp = pd.Series(timestamp, index=working.index)
        working["hour"] = _to_naive_hour(timestamp)
        working = working.dropna(subset=["hour"])

        if "ticker" in working.columns:
            working["ticker"] = working["ticker"].map(normalize_ticker)
        else:
            inferred = normalize_ticker(file_path.stem.split("_")[0])
            working["ticker"] = inferred

        required = {"open", "high", "low", "close", "volume"}
        missing = required - set(working.columns)
        if missing:
            raise ValueError(f"Missing price columns {sorted(missing)} in {file_path}")

        frames.append(
            working[["hour", "ticker", "open", "high", "low", "close", "volume"]]
        )

    price_df = pd.concat(frames, ignore_index=True)
    price_df = price_df.drop_duplicates(subset=["hour", "ticker"], keep="last")
    return price_df


def _load_fallback_csv(fallback_csv_path: Path) -> pd.DataFrame:
    fallback_csv_path = Path(fallback_csv_path)
    df = pd.read_csv(fallback_csv_path)
    if df.empty:
        raise ValueError("Fallback CSV is empty")

    if "timestamp" not in df.columns or "ticker" not in df.columns:
        raise ValueError("Fallback CSV missing required columns")

    working = df.copy()
    working["hour"] = _to_naive_hour(working["timestamp"])
    working = working.dropna(subset=["hour", "ticker"])
    working["ticker"] = working["ticker"].map(normalize_ticker)

    working["mean_score"] = working.get("sentiment_avg", 0.0)
    working["net_sentiment"] = 0.0
    working["text_count"] = 0

    return working[["hour", "ticker", "net_sentiment", "mean_score", "text_count"]]


def _build_fallback_sentiment(
    price_df: pd.DataFrame,
    fallback_path: Path = DEFAULT_FALLBACK_SENTIMENT_PATH,
    fallback_csv_path: Path = DEFAULT_FALLBACK_CSV_PATH,
) -> pd.DataFrame:
    fallback = price_df[["hour", "ticker"]].drop_duplicates().copy()
    fallback["net_sentiment"] = 0.0
    fallback["mean_score"] = 0.0
    fallback["text_count"] = 0

    fallback_path = Path(fallback_path)
    fallback_path.parent.mkdir(parents=True, exist_ok=True)
    fallback.to_parquet(fallback_path, index=False)

    fallback_csv = price_df.drop_duplicates(subset=["hour", "ticker"], keep="last").copy()
    fallback_csv = fallback_csv.rename(columns={"hour": "timestamp"})
    fallback_csv["adj_close"] = fallback_csv["close"]
    fallback_csv["sentiment_avg"] = 0.0
    fallback_csv["sentiment_label"] = "neutral"
    fallback_csv = fallback_csv[
        [
            "timestamp",
            "ticker",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "adj_close",
            "sentiment_avg",
            "sentiment_label",
        ]
    ]
    fallback_csv_path = Path(fallback_csv_path)
    if not fallback_csv_path.exists():
        fallback_csv_path.parent.mkdir(parents=True, exist_ok=True)
        fallback_csv.to_csv(fallback_csv_path, index=False)

    return fallback


def load_sentiment_data(
    sentiment_path: Path = DEFAULT_SENTIMENT_PATH,
    fallback_path: Path = DEFAULT_FALLBACK_SENTIMENT_PATH,
    fallback_csv_path: Path = DEFAULT_FALLBACK_CSV_PATH,
) -> pd.DataFrame:
    """Load hourly sentiment data."""
    logger = logging.getLogger(__name__)
    sentiment_path = Path(sentiment_path)
    if not sentiment_path.exists():
        logger.warning("Sentiment file missing at %s; using fallback data.", sentiment_path)
        fallback_csv_path = Path(fallback_csv_path)
        if fallback_csv_path.exists() and fallback_csv_path.stat().st_size > 0:
            return _load_fallback_csv(fallback_csv_path)
        price_df = load_price_data(DEFAULT_PRICE_DIR)
        return _build_fallback_sentiment(price_df, fallback_path, fallback_csv_path)

    sentiment_ts = pd.read_parquet(sentiment_path)
    if sentiment_ts.empty:
        logger.warning("Sentiment file is empty at %s; using fallback data.", sentiment_path)
        fallback_csv_path = Path(fallback_csv_path)
        if fallback_csv_path.exists() and fallback_csv_path.stat().st_size > 0:
            return _load_fallback_csv(fallback_csv_path)
        price_df = load_price_data(DEFAULT_PRICE_DIR)
        return _build_fallback_sentiment(price_df, fallback_path, fallback_csv_path)

    for col in ("hour", "ticker", "net_sentiment", "mean_score", "text_count"):
        if col not in sentiment_ts.columns:
            raise ValueError(f"Missing sentiment column: {col}")

    sentiment_ts = sentiment_ts.copy()
    sentiment_ts["hour"] = _to_naive_hour(sentiment_ts["hour"])
    sentiment_ts = sentiment_ts.dropna(subset=["hour"])
    sentiment_ts["ticker"] = sentiment_ts["ticker"].map(normalize_ticker)

    return sentiment_ts[["hour", "ticker", "net_sentiment", "mean_score", "text_count"]]


def prepare_feature_frame(
    price_df: pd.DataFrame,
    sentiment_ts: pd.DataFrame,
    missing_strategy: str = "fill",
    add_technical_indicators: bool = False,
) -> pd.DataFrame:
    """Merge price and sentiment data and compute features."""
    if missing_strategy not in {"fill", "drop"}:
        raise ValueError("missing_strategy must be 'fill' or 'drop'")

    price_df = price_df.copy()
    price_df["hour"] = _to_naive_hour(price_df["hour"])
    price_df = price_df.dropna(subset=["hour", "ticker"])
    price_df["ticker"] = price_df["ticker"].map(normalize_ticker)

    sentiment_ts = sentiment_ts.copy()
    sentiment_ts["hour"] = _to_naive_hour(sentiment_ts["hour"])
    sentiment_ts = sentiment_ts.dropna(subset=["hour", "ticker"])
    sentiment_ts["ticker"] = sentiment_ts["ticker"].map(normalize_ticker)

    merged = price_df.merge(sentiment_ts, on=["hour", "ticker"], how="left")
    if add_technical_indicators:
        # Indicators are computed for analysis; FEATURE_COLUMNS stays unchanged for inference parity.
        from src.features.technical_indicators import add_all_technical_indicators

        merged = add_all_technical_indicators(merged)
    merged["net_sentiment"] = merged["net_sentiment"].fillna(0.0)
    merged["mean_score"] = merged["mean_score"].fillna(0.0)
    merged["text_count"] = merged["text_count"].fillna(0.0)

    merged = merged.sort_values(["ticker", "hour"]).reset_index(drop=True)

    if missing_strategy == "fill":
        price_cols = ["open", "high", "low", "close", "volume"]
        merged[price_cols] = merged.groupby("ticker")[price_cols].ffill()

    merged["returns_1h"] = (
        merged.groupby("ticker")["close"].pct_change().fillna(0.0)
    )
    merged["volatility_6h"] = (
        merged.groupby("ticker")["returns_1h"]
        .rolling(window=6, min_periods=1)
        .std(ddof=0)
        .reset_index(level=0, drop=True)
        .fillna(0.0)
    )

    merged["future_return"] = merged.groupby("ticker")["returns_1h"].shift(-1)
    merged["label"] = np.where(
        merged["future_return"].isna(),
        np.nan,
        (merged["future_return"] > 0).astype(float),
    )

    merged["trend_target"] = merged["future_return"]
    merged["future_abs_return"] = merged.groupby("ticker")["returns_1h"].shift(-1).abs()
    merged["volatility_target"] = np.where(
        merged["future_abs_return"].isna(),
        np.nan,
        (merged["future_abs_return"] >= 0.02).astype(float),
    )

    if missing_strategy == "drop":
        merged = merged.dropna(
            subset=FEATURE_COLUMNS + ["label", "trend_target", "volatility_target"]
        )
    else:
        merged[FEATURE_COLUMNS] = merged[FEATURE_COLUMNS].fillna(0.0)
        merged = merged.dropna(subset=["label", "trend_target", "volatility_target"])

    return merged


def build_sliding_windows(
    feature_frame: pd.DataFrame,
    window_size: int = 24,
    normalize: bool = False,
    target_column: str = "label",
) -> Tuple[np.ndarray, np.ndarray]:
    """Construct sliding window tensors and labels."""
    if window_size <= 0:
        raise ValueError("window_size must be positive")

    if target_column not in feature_frame.columns:
        raise ValueError(f"target_column '{target_column}' not found in feature frame")

    features: List[np.ndarray] = []
    labels: List[float] = []

    for _, group in feature_frame.groupby("ticker"):
        group = group.sort_values("hour").reset_index(drop=True)
        if len(group) < window_size:
            continue

        feature_array = group[FEATURE_COLUMNS].to_numpy(dtype=np.float32)
        label_array = group[target_column].to_numpy(dtype=np.float32)

        for start in range(0, len(group) - window_size + 1):
            end = start + window_size
            features.append(feature_array[start:end])
            labels.append(label_array[end - 1])

    if not features:
        empty_features = np.empty((0, window_size, len(FEATURE_COLUMNS)), dtype=np.float32)
        empty_labels = np.empty((0,), dtype=np.float32)
        if normalize:
            # Normalization disabled to keep training/inference parity.
            return empty_features, empty_labels, None
        return empty_features, empty_labels

    features_array = np.stack(features)
    labels_array = np.array(labels, dtype=np.float32)
    if normalize:
        # Normalization disabled to keep training/inference parity.
        return features_array, labels_array, None
    return features_array, labels_array


def split_dataset(
    features: np.ndarray,
    labels: np.ndarray,
    train_frac: float = 0.7,
    val_frac: float = 0.15,
) -> Tuple[Tuple[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray]]:
    """Split arrays into train/validation/test without shuffling."""
    total = len(features)
    if total == 0:
        raise ValueError("No samples available for splitting")

    train_end = int(total * train_frac)
    val_end = train_end + int(total * val_frac)
    if train_end == 0 or val_end <= train_end or val_end >= total:
        raise ValueError("Not enough samples to split into train/val/test")

    train = (features[:train_end], labels[:train_end])
    val = (features[train_end:val_end], labels[train_end:val_end])
    test = (features[val_end:], labels[val_end:])
    return train, val, test


def create_dataloaders(
    train: Tuple[np.ndarray, np.ndarray],
    val: Tuple[np.ndarray, np.ndarray],
    test: Tuple[np.ndarray, np.ndarray],
    batch_size: int = 64,
) -> Dict[str, DataLoader]:
    """Create DataLoaders for each split."""
    train_loader = DataLoader(
        TimeSeriesDataset(*train), batch_size=batch_size, shuffle=False
    )
    val_loader = DataLoader(TimeSeriesDataset(*val), batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(
        TimeSeriesDataset(*test), batch_size=batch_size, shuffle=False
    )
    return {"train": train_loader, "val": val_loader, "test": test_loader}


def _evaluate_loader(
    model: nn.Module, loader: DataLoader, device: str
) -> Tuple[Dict[str, float], np.ndarray, np.ndarray]:
    model.eval()
    all_probs: List[float] = []
    all_labels: List[float] = []

    with torch.no_grad():
        for batch_features, batch_labels in loader:
            batch_features = batch_features.to(device)
            batch_labels = batch_labels.to(device)
            probs = model(batch_features).squeeze(1)
            all_probs.extend(probs.detach().cpu().numpy().tolist())
            all_labels.extend(batch_labels.detach().cpu().numpy().tolist())

    metrics = compute_metrics(np.array(all_labels), np.array(all_probs))
    return metrics, np.array(all_probs), np.array(all_labels)


def compute_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> Dict[str, float]:
    """Compute binary classification metrics."""
    y_pred = (y_prob >= 0.5).astype(int)
    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
    }

    try:
        metrics["auc_roc"] = float(roc_auc_score(y_true, y_prob))
    except ValueError:
        metrics["auc_roc"] = float("nan")

    return metrics


def train_model(
    model: nn.Module,
    loaders: Dict[str, DataLoader],
    config: TrainingConfig,
    save_path: Optional[Path] = None,
    on_epoch_end: Optional[Callable[[int, Dict[str, float]], None]] = None,
) -> Tuple[nn.Module, Dict[str, float]]:
    """Train a model with early stopping on validation F1."""
    device = config.device
    model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    criterion = nn.BCELoss()

    best_state = None
    best_f1 = float("-inf")
    epochs_without_improve = 0

    for epoch in range(1, config.epochs + 1):
        model.train()
        running_loss = 0.0
        for batch_features, batch_labels in loaders["train"]:
            batch_features = batch_features.to(device)
            batch_labels = batch_labels.to(device)

            optimizer.zero_grad()
            outputs = model(batch_features).squeeze(1)
            loss = criterion(outputs, batch_labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * batch_features.size(0)

        train_loss = running_loss / max(len(loaders["train"].dataset), 1)
        val_metrics, _, _ = _evaluate_loader(model, loaders["val"], device)

        epoch_metrics = {
            "train_loss": float(train_loss),
            "val_accuracy": val_metrics["accuracy"],
            "val_f1": val_metrics["f1"],
        }
        if on_epoch_end:
            on_epoch_end(epoch, epoch_metrics)

        if val_metrics["f1"] > best_f1:
            best_f1 = val_metrics["f1"]
            best_state = copy.deepcopy(model.state_dict())
            epochs_without_improve = 0
            if save_path is not None:
                save_path.parent.mkdir(parents=True, exist_ok=True)
                torch.save(best_state, save_path)
        else:
            epochs_without_improve += 1

        if epochs_without_improve >= config.patience:
            break

    if best_state is not None:
        model.load_state_dict(best_state)

    return model, {"best_f1": float(best_f1)}


def run_experiment(
    model_spec: ModelSpec,
    loaders: Dict[str, DataLoader],
    config: TrainingConfig,
    model_dir: Path,
    artifact_dir: Path,
    mlflow_enabled: bool = True,
) -> Dict[str, float]:
    """Train a single model, log metrics, and evaluate on the test set."""
    input_size = loaders["train"].dataset.features.shape[-1]
    model = model_spec.constructor(input_size=input_size)
    model_path = model_dir / f"{model_spec.name.lower()}_best.pt"

    def log_epoch(epoch: int, metrics: Dict[str, float]) -> None:
        if not mlflow_enabled:
            return
        mlflow.log_metric("train_loss", metrics["train_loss"], step=epoch)
        mlflow.log_metric("val_accuracy", metrics["val_accuracy"], step=epoch)
        mlflow.log_metric("val_f1", metrics["val_f1"], step=epoch)

    if mlflow_enabled:
        mlflow.log_param("model", model_spec.name)
        mlflow.log_param("learning_rate", config.learning_rate)
        mlflow.log_param("window_size", config.window_size)
        mlflow.log_param("hidden_size", model_spec.hidden_size)
        mlflow.log_param("batch_size", config.batch_size)
        mlflow.log_param("epochs", config.epochs)
        mlflow.log_param("patience", config.patience)

    model, _ = train_model(
        model,
        loaders,
        config,
        save_path=model_path,
        on_epoch_end=log_epoch,
    )

    test_metrics, probs, labels = _evaluate_loader(model, loaders["test"], config.device)

    if mlflow_enabled:
        mlflow.log_metric("test_accuracy", test_metrics["accuracy"])
        mlflow.log_metric("test_f1", test_metrics["f1"])
        mlflow.log_metric("test_precision", test_metrics["precision"])
        mlflow.log_metric("test_recall", test_metrics["recall"])
        mlflow.log_metric("test_auc_roc", test_metrics["auc_roc"])
        mlflow.pytorch.log_model(model, artifact_path="model")

    artifact_dir.mkdir(parents=True, exist_ok=True)
    preds_path = artifact_dir / f"{model_spec.name.lower()}_test_predictions.csv"
    metrics_path = artifact_dir / f"{model_spec.name.lower()}_test_metrics.json"

    preds_df = pd.DataFrame(
        {"y_true": labels.astype(int), "y_prob": probs, "y_pred": (probs >= 0.5)}
    )
    preds_df.to_csv(preds_path, index=False)
    metrics_path.write_text(pd.Series(test_metrics).to_json())

    if mlflow_enabled:
        mlflow.log_artifact(str(preds_path))
        mlflow.log_artifact(str(metrics_path))

    results = {"model": model_spec.name}
    results.update(test_metrics)
    # RMSE not applicable – only direction classification was performed.
    results["rmse"] = float("nan")
    if mlflow_enabled:
        mlflow.log_metric("rmse", results["rmse"])
    return results


def run_all_models(
    loaders: Dict[str, DataLoader],
    config: TrainingConfig,
    model_dir: Path,
    artifact_dir: Path,
    mlflow_enabled: bool = True,
) -> List[Dict[str, float]]:
    """Run training for all model specs."""
    results: List[Dict[str, float]] = []

    for model_spec in MODEL_SPECS:
        if mlflow_enabled:
            with mlflow.start_run(run_name=model_spec.name):
                result = run_experiment(
                    model_spec,
                    loaders,
                    config,
                    model_dir=model_dir,
                    artifact_dir=artifact_dir,
                    mlflow_enabled=mlflow_enabled,
                )
        else:
            result = run_experiment(
                model_spec,
                loaders,
                config,
                model_dir=model_dir,
                artifact_dir=artifact_dir,
                mlflow_enabled=mlflow_enabled,
            )
        results.append(result)

    return results


def format_comparison_table(results: List[Dict[str, float]]) -> str:
    """Format a comparison table from results."""
    header = "Model | Accuracy | F1 | RMSE"
    divider = "-" * len(header)
    lines = [header, divider]

    for result in results:
        rmse = result.get("rmse")
        if rmse is None or (isinstance(rmse, float) and math.isnan(rmse)):
            rmse_text = "N/A"
        else:
            rmse_text = f"{rmse:.4f}"
        line = (
            f"{result['model']:<4} | {result['accuracy']:.4f} | "
            f"{result['f1']:.4f} | {rmse_text}"
        )
        lines.append(line)

    return "\n".join(lines)
