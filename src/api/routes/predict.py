"""Prediction endpoint."""

from fastapi import APIRouter, HTTPException

from ..services.feature_pipeline import get_latest_features, normalize_ticker
from ..services.model_loader import get_model, predict_direction
from ..utils.time import utc_now_iso

router = APIRouter()


@router.get("/{ticker}")
def predict(ticker: str) -> dict:
    """Return the next-hour direction prediction."""
    ticker = normalize_ticker(ticker)

    try:
        features = get_latest_features(ticker)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    try:
        model, model_name = get_model("LSTM")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Model load failed: {exc}") from exc

    direction, confidence = predict_direction(model, features)

    return {
        "ticker": ticker,
        "direction": direction,
        "confidence": round(confidence, 4),
        "model": model_name,
        "timestamp": utc_now_iso(),
    }
