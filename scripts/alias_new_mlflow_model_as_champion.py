import argparse
import os

import mlflow
from dotenv import load_dotenv
from loguru import logger
from mlflow.tracking import MlflowClient


def main():
    parser = argparse.ArgumentParser(
        description="Register a new model version and set it as the champion."
    )
    parser.add_argument("--run_id", type=str, required=True, help="ID of the run")
    parser.add_argument(
        "--model_name", type=str, required=True, help="Name of the model"
    )
    parser.add_argument(
        "--env", type=str, default="dev", help="Environment to load .env file"
    )

    args = parser.parse_args()

    root_dir = os.path.abspath(os.path.join(__file__, ".."))
    load_dotenv(f"{root_dir}/.env.{args.env}")

    run_id = args.run_id

    # Set your model details
    model_name = args.model_name
    model_uri = f"runs:/{run_id}/ner_aspect"

    # Initialize MLflow client
    client = MlflowClient()

    # Fetch run information
    run_info = client.get_run(run_id)
    logger.info("Run Information:")
    logger.info(f"Run ID: {run_info.info.run_id}")
    logger.info(f"Experiment ID: {run_info.info.experiment_id}")
    logger.info(f"Status: {run_info.info.status}")
    logger.info(f"Start Time: {run_info.info.start_time}")
    logger.info(f"End Time: {run_info.info.end_time}")

    # Fetch current champion alias information
    current_champion = client.get_model_version_by_alias(model_name, "champion")
    logger.info(f"Current Champion Model Version: {current_champion.version}")
    logger.info(f"Current Champion Model Run ID: {current_champion.run_id}")

    # Register the model
    model_version = mlflow.register_model(model_uri=model_uri, name=model_name)

    # Set the alias 'champion' to the new version
    client.set_registered_model_alias(
        name=model_name, alias="champion", version=model_version.version
    )

    # Check new champion alias information
    new_champion = client.get_model_version_by_alias(model_name, "champion")
    logger.info(f"New Champion Model Version: {new_champion.version}")
    logger.info(f"New Champion Model Run ID: {new_champion.run_id}")

    logger.info(f"Model version {model_version.version} is now the champion.")


if __name__ == "__main__":
    main()
