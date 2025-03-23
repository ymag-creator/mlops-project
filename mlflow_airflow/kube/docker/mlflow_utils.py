# -*- coding: utf-8 -*-
import logging
import os
import sys
import joblib
import numpy as np
from mlflow import MlflowClient
import mlflow
from mlflow.artifacts import download_artifacts
import mlflow.sklearn
import requests

in_container=True
if len(sys.argv) > 1:
    in_container = sys.argv[1]

def get_modelversion_by_alias(client, model_name, alias):
    try:
        # récupére la derniere version du modèle avec cette alias
        # type <<ModelVersion>
        modelversion = client.get_model_version_by_alias(model_name, alias)
        return modelversion
    except:
        return None


def get_registered_model(client, model_name):
    try:
        # récupére le model et des infos : dernier update, l'instance de la dernière version : .latest_versions
        # type <RegisteredModel>
        last_model = client.get_registered_model(model_name)
        return last_model
    except:
        return None


def load_model_from_mlflow(
    in_container=True
):
    print("in_container", in_container)

    # récupère la dernière expérience en prod
    if in_container == True:
        server_adress = "http://host.docker.internal:5000"  # "http://172.25.0.100:5000"
        print(requests.get("http://host.docker.internal:5000"))
    else:
        server_adress = "http://localhost:5000"
    print(server_adress)

    print("client")
    client = MlflowClient(tracking_uri=server_adress)
    print("set_tracking_uri")
    mlflow.set_tracking_uri(uri=server_adress)
    print("mlflow connected")

    model_name = "Projet_MlOps"
    production_alias = "Production"
    to_deploy__alias = "A_Deployer"
    mlflow.set_experiment("Projet_MlOps")

    artifact_path = "train_for_prod"

    # Retrouve la dernière version en prod et l'experience correspondante
    model_version = get_modelversion_by_alias(client, model_name, to_deploy__alias)
    # vérifie avec le dernier model du repo la variation du score
    if model_version and model_version.run_id:
        run = mlflow.get_run(model_version.run_id)
        print(run)
        # charge le model
        artifact_uri = run.info.artifact_uri
        print(f"Artifact URI: {artifact_uri}")
        if in_container:
            dest = "data/model"
        else:
            dest = "C:/Users/lordb/OneDrive/Documents/PTP/Projet MLOps/Projet_MLOps_accidents/mlflow_airflow/kube/docker/model"
        # # charge le model
        # champion_version = mlflow.pyfunc.load_model(
        #     f"models:/{model_name}@{to_deploy__alias}"
        # )
        # print(champion_version)
        # model = mlflow.sklearn.load_model(       # Le load model charge tout le réperrtoire, long et des blocage dans le container
        #     f"runs:/{model_version.run_id}/{artifact_path}", dst_path=dest
        # )

        local_path = client.download_artifacts(
            model_version.run_id, "train_for_prod/model.pkl", dst_path=dest
        )
        model = joblib.load(local_path)

        print(model)
        # charge le scaler
        scaler_path = download_artifacts(
            run_id=model_version.run_id, artifact_path="scaler.pkl", dst_path=dest
        )
        # Charger le .pkl
        with open(scaler_path, "rb") as f:
            scaler = joblib.load(f)
        print(scaler)
        return model, scaler
    else:
        print("pas de Model")
        return None, None


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    # project_dir = Path(__file__).resolve().parents[2]
    load_model_from_mlflow(False)
