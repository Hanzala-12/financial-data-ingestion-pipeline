"""Prediction endpoints."""

from datetime import date as date_type

from fastapi import APIRouter, HTTPException, Query

from ..services.feature_pipeline import get_latest_features, normalize_ticker
from ..services.model_loader import (
    get_model,
    get_task_model,
    predict_direction,
    predict_probability,
    predict_regression_value,
)
from ..utils.time import utc_now_iso

router = APIRouter()


def _predict_payload(ticker: str, requested_date: str | None = None) -> dict:
    """Build a prediction response for the requested ticker."""
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

    try:
        trend_model, trend_model_name = get_task_model("trend", "LSTM")
        trend_score = predict_regression_value(trend_model, features)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Trend model load failed: {exc}") from exc

    try:
        volatility_model, volatility_model_name = get_task_model("volatility", "LSTM")
        volatility_probability = predict_probability(volatility_model, features)
        volatility_spike = volatility_probability >= 0.5
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Volatility model load failed: {exc}") from exc

    return {
        "ticker": ticker,
        "date": requested_date,
        "direction": direction,
        "market_direction": direction,
        "confidence": round(confidence, 4),
        "price_trend": {
            "value": round(float(trend_score), 6),
            "model": trend_model_name,
            "interpretation": "Positive values indicate an expected upward next-step return.",
        },
        "volatility_spike": {
            "predicted": volatility_spike,
            "probability": round(volatility_probability, 6),
            "model": volatility_model_name,
        },
        "model": model_name,
        "timestamp": utc_now_iso(),
    }


@router.get("")
def predict(
    ticker: str = Query(..., min_length=1),
    date: date_type | None = None,
) -> dict:
    """Return the next-hour direction prediction for a ticker/date request."""
    requested_date = date.isoformat() if date else None
    return _predict_payload(ticker, requested_date=requested_date)


@router.post("")
def predict_post(payload: dict) -> dict:
    """Support JSON-based prediction requests for the static frontend."""
    ticker = payload.get("ticker")
    if not ticker:
        raise HTTPException(status_code=400, detail="ticker is required")

    requested_date = payload.get("date")
    return _predict_payload(ticker, requested_date=requested_date)


@router.get("/{ticker}")
def predict_legacy(ticker: str) -> dict:
    """Backward-compatible ticker-only route used by the existing React client."""
    return _predict_payload(ticker)
