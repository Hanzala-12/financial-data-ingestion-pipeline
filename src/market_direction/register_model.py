"""Model registration script for MLflow.
Finds the best model and registers it to the 'Production' stage.
"""

import sys
import mlflow
from mlflow.tracking import MlflowClient

def register_best_model(experiment_name: str = "market_direction"):
    client = MlflowClient()
    experiment = client.get_experiment_by_name(experiment_name)
    if not experiment:
        print(f"Experiment '{experiment_name}' not found.")
        sys.exit(1)

    # Search for runs, sorted by test_f1 descending
    runs = client.search_runs(
        [experiment.experiment_id],
        order_by=["metrics.test_f1 DESC"],
        max_results=10
    )

    if not runs:
        print("No runs found to register.")
        sys.exit(1)

    best_run = runs[0]
    best_f1 = best_run.data.metrics.get("test_f1", 0.0)
    model_type = best_run.data.params.get("model", "UNKNOWN")
    run_id = best_run.info.run_id

    print(f"Best Run ID: {run_id} | Model: {model_type} | Test F1: {best_f1:.4f}")

    # Register the model
    model_name = model_type.upper()
    model_uri = f"runs:/{run_id}/model"
    
    try:
        registered_model = mlflow.register_model(model_uri, model_name)
        print(f"Successfully registered model '{model_name}' (Version {registered_model.version})")
        
        # Transition to Production
        client.transition_model_version_stage(
            name=model_name,
            version=registered_model.version,
            stage="Production",
            archive_existing_versions=True
        )
        print(f"Transitioned model '{model_name}' v{registered_model.version} to Production.")
    except Exception as e:
        print(f"Error registering model: {e}")

if __name__ == "__main__":
    register_best_model()
