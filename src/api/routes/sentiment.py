"""Sentiment endpoint."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.sentiment_loader import load_recent_sentiment
from src.sentiment.vader_model import classify_vader

router = APIRouter()

class TextPayload(BaseModel):
    text: str


@router.get("/{ticker}")
def sentiment(ticker: str):
    """Return recent sentiment points for a ticker."""
    try:
        return load_recent_sentiment(ticker)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/analyze")
def analyze(payload: TextPayload):
    """Analyze a single headline and return its sentiment & directional prediction."""
    text = payload.text
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    
    label, score = classify_vader(text)
    
    # We create a dummy directional output based heavily on the sentiment score
    # since we don't have the OHLCV features to feed the RNN for a single headline.
    direction = "UP" if score >= 0.05 else "DOWN" if score <= -0.05 else "FLAT"
    confidence = abs(score) # Use sentiment confidence as a proxy
    
    return {
        "text": text,
        "sentiment": {
            "label": label,
            "score": round(score, 4)
        },
        "predicted_direction": direction,
        "confidence": confidence
    }
