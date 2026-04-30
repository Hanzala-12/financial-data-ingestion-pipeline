"""Model comparison endpoint."""

from fastapi import APIRouter

from ..services.model_loader import list_models

router = APIRouter()


@router.get("/")
def models():
    """Return metrics for available models."""
    return list_models()
