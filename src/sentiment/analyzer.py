"""Sentiment analysis helper expected by the project layout."""

from pathlib import Path
from typing import Iterable, List, Literal

from .config import SentimentConfig
from .finbert_model import classify_finbert
from .processor import run_sentiment_pipeline
from .vader_model import classify_vader

Backend = Literal["vader", "finbert"]


def analyze_text(text: str, backend: Backend = "vader") -> dict:
    """Classify a single text string with the requested backend."""
    if backend == "finbert":
        label, score = classify_finbert(text)
    else:
        label, score = classify_vader(text)

    return {"label": label, "score": round(float(score), 4), "backend": backend}



def analyze_texts(texts: Iterable[str], backend: Backend = "vader") -> List[dict]:
    """Classify multiple texts and return structured results."""
    return [analyze_text(text, backend=backend) for text in texts]



def main() -> None:
    """Run the full sentiment pipeline."""
    run_sentiment_pipeline()


if __name__ == "__main__":
    main()
