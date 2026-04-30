"""Model loading and registry helpers."""

from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple
import json

import torch
import mlflow
import mlflow.pytorch
from mlflow.exceptions import MlflowException
from mlflow.tracking import MlflowClient

from src.market_direction.pipeline import FEATURE_COLUMNS, GRUModel, LSTMModel, RNNModel

_MODEL_CLASSES = {
    "RNN": RNNModel,
    "LSTM": LSTMModel,
    "GRU": GRUModel,
}


def _load_mlflow_model(model_name: str) -> torch.nn.Module:
    model_uri = f"models:/{model_name}/Production"
    return mlflow.pytorch.load_model(model_uri)


def _load_local_model(model_name: str) -> torch.nn.Module:
    model_path = Path("models") / f"{model_name.lower()}_best.pt"
    if not model_path.exists():
        raise FileNotFoundError(f"Local model not found at {model_path}")

    model_class = _MODEL_CLASSES.get(model_name)
    if model_class is None:
        raise ValueError(f"Unsupported model name: {model_name}")

    model = model_class(input_size=len(FEATURE_COLUMNS))
    state = torch.load(model_path, map_location="cpu")
    model.load_state_dict(state)
    return model


@lru_cache(maxsize=3)
def get_model(model_name: str = "LSTM") -> Tuple[torch.nn.Module, str]:
    """Load and cache a model by name."""
    model_name = model_name.upper()
    try:
        model = _load_mlflow_model(model_name)
    except (MlflowException, OSError, FileNotFoundError, ValueError):
        model = _load_local_model(model_name)

    model.eval()
    return model, model_name


def predict_direction(model: torch.nn.Module, features) -> Tuple[str, float]:
    """Predict direction and confidence from model output."""
    tensor = torch.tensor(features, dtype=torch.float32)
    with torch.no_grad():
        prob = model(tensor).squeeze().item()

    direction = "UP" if prob >= 0.5 else "DOWN"
    confidence = prob if direction == "UP" else 1.0 - prob
    return direction, float(confidence)


def list_models(experiment_name: str = "market_direction") -> List[Dict[str, float]]:
    """List model metrics from MLflow with artifact fallback."""
    try:
        results = _list_models_from_mlflow(experiment_name)
    except MlflowException:
        results = []

    if results:
        return results

    return _list_models_from_artifacts()


def _list_models_from_mlflow(experiment_name: str) -> List[Dict[str, float]]:
    client = MlflowClient()
    experiment = client.get_experiment_by_name(experiment_name)
    if not experiment:
        return []

    runs = client.search_runs(
        [experiment.experiment_id],
        order_by=["attributes.start_time DESC"],
        max_results=50,
    )

    latest_by_model = {}
    for run in runs:
        model_name = run.data.params.get("model")
        if not model_name:
            continue
        if model_name in latest_by_model:
            continue
        latest_by_model[model_name] = run

    summaries = []
    for model_name, run in latest_by_model.items():
        metrics = run.data.metrics
        summaries.append(
            {
                "name": model_name,
                "run_id": run.info.run_id,
                "accuracy": _pick_metric(metrics, "val_accuracy", "test_accuracy"),
                "f1": _pick_metric(metrics, "val_f1", "test_f1"),
                "rmse": _pick_metric(metrics, "rmse", "test_rmse", "val_rmse"),
            }
        )

    return summaries


def _list_models_from_artifacts(artifact_dir: Path = Path("artifacts")) -> List[Dict[str, float]]:
    summaries: List[Dict[str, float]] = []
    if not artifact_dir.exists():
        return summaries

    for path in artifact_dir.glob("*_test_metrics.json"):
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue

        name = path.stem.replace("_test_metrics", "").upper()
        summaries.append(
            {
                "name": name,
                "run_id": None,
                "accuracy": data.get("accuracy"),
                "f1": data.get("f1"),
                "rmse": data.get("rmse"),
            }
        )

    return summaries


def _pick_metric(metrics: Dict[str, float], *keys: str):
    for key in keys:
        value = metrics.get(key)
        if value is not None:
            return float(value)
    return None
