"""FastAPI entrypoint for ML serving."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .routes import models, predict, retrain, sentiment

app = FastAPI(title="ML Serving API", version="0.1.0")

STATIC_DIR = Path(__file__).resolve().parent / "static"

origins = ["http://localhost:3000", "http://localhost:5173"]

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

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def root() -> FileResponse:
    """Serve the simple manual testing frontend."""
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=500, detail="Static frontend is missing")
    return FileResponse(path=str(index_file))


@app.get("/health")
def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}
