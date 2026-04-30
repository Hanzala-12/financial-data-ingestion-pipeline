"""Sentiment endpoint."""

from fastapi import APIRouter, HTTPException

from ..services.sentiment_loader import load_recent_sentiment

router = APIRouter()


@router.get("/{ticker}")
def sentiment(ticker: str):
    """Return recent sentiment points for a ticker."""
    try:
        return load_recent_sentiment(ticker)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
