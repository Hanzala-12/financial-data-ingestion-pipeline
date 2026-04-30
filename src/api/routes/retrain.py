"""Model retraining endpoint (admin only)."""

from fastapi import APIRouter, BackgroundTasks

from ..services.training_service import retrain_models

router = APIRouter()


@router.post("/")
def retrain(background_tasks: BackgroundTasks) -> dict:
    """Trigger retraining in the background."""
    background_tasks.add_task(retrain_models)
    return {
        "status": "scheduled",
        "detail": "Retraining triggered (admin only).",
    }
