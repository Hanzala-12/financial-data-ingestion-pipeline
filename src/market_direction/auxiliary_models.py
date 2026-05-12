"""Auxiliary sequence models for trend regression and task-specific inference."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple
import copy

import mlflow
import mlflow.pytorch
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from torch import nn
from torch.utils.data import DataLoader


class TrendLSTM(nn.Module):
    """LSTM regressor for next-step price trend."""

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

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        output, _ = self.lstm(inputs)
        output = output[:, -1, :]
        return self.fc(output).squeeze(-1)


@dataclass
class RegressionTrainingResult:
    """Container for regression training outputs."""

    best_rmse: float
    metrics: Dict[str, float]


class _RegressionDataset(torch.utils.data.Dataset):
    def __init__(self, features: np.ndarray, labels: np.ndarray) -> None:
        self.features = torch.tensor(features, dtype=torch.float32)
        self.labels = torch.tensor(labels, dtype=torch.float32)

    def __len__(self) -> int:
        return len(self.features)

    def __getitem__(self, index: int) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.features[index], self.labels[index]


def create_regression_dataloaders(
    train: Tuple[np.ndarray, np.ndarray],
    val: Tuple[np.ndarray, np.ndarray],
    test: Tuple[np.ndarray, np.ndarray],
    batch_size: int = 64,
) -> Dict[str, DataLoader]:
    """Create data loaders for regression targets."""
    return {
        "train": DataLoader(_RegressionDataset(*train), batch_size=batch_size, shuffle=False),
        "val": DataLoader(_RegressionDataset(*val), batch_size=batch_size, shuffle=False),
        "test": DataLoader(_RegressionDataset(*test), batch_size=batch_size, shuffle=False),
    }


def compute_regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Compute standard regression metrics."""
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))
    try:
        r2 = float(r2_score(y_true, y_pred))
    except ValueError:
        r2 = float("nan")
    return {"rmse": rmse, "mae": mae, "r2": r2}


def _evaluate_regression_loader(
    model: nn.Module,
    loader: DataLoader,
    device: str,
) -> Tuple[Dict[str, float], np.ndarray, np.ndarray]:
    model.eval()
    predictions: List[float] = []
    targets: List[float] = []

    with torch.no_grad():
        for batch_features, batch_labels in loader:
            batch_features = batch_features.to(device)
            batch_labels = batch_labels.to(device)
            outputs = model(batch_features).reshape(-1)
            predictions.extend(outputs.detach().cpu().numpy().tolist())
            targets.extend(batch_labels.detach().cpu().numpy().tolist())

    metrics = compute_regression_metrics(np.array(targets), np.array(predictions))
    return metrics, np.array(predictions), np.array(targets)


def train_regression_model(
    model: nn.Module,
    loaders: Dict[str, DataLoader],
    learning_rate: float,
    epochs: int,
    patience: int,
    device: str,
    save_path: Optional[Path] = None,
    on_epoch_end: Optional[Callable[[int, Dict[str, float]], None]] = None,
) -> Tuple[nn.Module, Dict[str, float]]:
    """Train a regression model with early stopping on validation RMSE."""
    model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    criterion = nn.MSELoss()

    best_state = None
    best_rmse = float("inf")
    epochs_without_improve = 0

    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        for batch_features, batch_labels in loaders["train"]:
            batch_features = batch_features.to(device)
            batch_labels = batch_labels.to(device)

            optimizer.zero_grad()
            outputs = model(batch_features).reshape(-1)
            loss = criterion(outputs, batch_labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * batch_features.size(0)

        train_loss = running_loss / max(len(loaders["train"].dataset), 1)
        val_metrics, _, _ = _evaluate_regression_loader(model, loaders["val"], device)

        epoch_metrics = {
            "train_loss": float(train_loss),
            "val_rmse": float(val_metrics["rmse"]),
            "val_mae": float(val_metrics["mae"]),
        }
        if on_epoch_end:
            on_epoch_end(epoch, epoch_metrics)

        if val_metrics["rmse"] < best_rmse:
            best_rmse = float(val_metrics["rmse"])
            best_state = copy.deepcopy(model.state_dict())
            epochs_without_improve = 0
            if save_path is not None:
                save_path.parent.mkdir(parents=True, exist_ok=True)
                torch.save(best_state, save_path)
        else:
            epochs_without_improve += 1

        if epochs_without_improve >= patience:
            break

    if best_state is not None:
        model.load_state_dict(best_state)

    return model, {"best_rmse": float(best_rmse)}


def run_trend_experiment(
    model_name: str,
    input_size: int,
    loaders: Dict[str, DataLoader],
    learning_rate: float,
    epochs: int,
    patience: int,
    device: str,
    model_dir: Path,
    artifact_dir: Path,
    mlflow_enabled: bool = True,
) -> Dict[str, float]:
    """Train and evaluate the trend regression model."""
    model = TrendLSTM(input_size=input_size)
    model_path = model_dir / f"{model_name.lower()}_best.pt"

    def log_epoch(epoch: int, metrics: Dict[str, float]) -> None:
        if not mlflow_enabled:
            return
        mlflow.log_metric("train_loss", metrics["train_loss"], step=epoch)
        mlflow.log_metric("val_rmse", metrics["val_rmse"], step=epoch)
        mlflow.log_metric("val_mae", metrics["val_mae"], step=epoch)

    model, _ = train_regression_model(
        model,
        loaders,
        learning_rate=learning_rate,
        epochs=epochs,
        patience=patience,
        device=device,
        save_path=model_path,
        on_epoch_end=log_epoch,
    )

    test_metrics, predictions, labels = _evaluate_regression_loader(model, loaders["test"], device)

    artifact_dir.mkdir(parents=True, exist_ok=True)
    preds_path = artifact_dir / f"{model_name.lower()}_test_predictions.csv"
    metrics_path = artifact_dir / f"{model_name.lower()}_test_metrics.json"
    preds_df = pd.DataFrame({"y_true": labels, "y_pred": predictions})
    preds_df.to_csv(preds_path, index=False)
    metrics_path.write_text(pd.Series(test_metrics).to_json())

    if mlflow_enabled:
        mlflow.log_metric("test_rmse", test_metrics["rmse"])
        mlflow.log_metric("test_mae", test_metrics["mae"])
        mlflow.log_metric("test_r2", test_metrics["r2"])
        mlflow.pytorch.log_model(model, artifact_path="model")
        mlflow.log_artifact(str(preds_path))
        mlflow.log_artifact(str(metrics_path))

    results = {"model": model_name}
    results.update(test_metrics)
    return results


def predict_regression(model: nn.Module, features) -> float:
    """Predict a scalar regression value from sequence features."""
    tensor = torch.tensor(features, dtype=torch.float32)
    with torch.no_grad():
        value = model(tensor).reshape(-1).item()
    return float(value)
