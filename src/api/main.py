"""FastAPI entrypoint for ML serving."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import models, predict, retrain, sentiment

app = FastAPI(title="ML Serving API", version="0.1.0")

origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict.router, prefix="/predict", tags=["predict"])
app.include_router(sentiment.router, prefix="/sentiment", tags=["sentiment"])
app.include_router(models.router, prefix="/models", tags=["models"])
app.include_router(retrain.router, prefix="/retrain", tags=["retrain"])


@app.get("/health")
def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}
