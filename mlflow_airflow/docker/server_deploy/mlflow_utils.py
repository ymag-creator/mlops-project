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


def set_production_alias(
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
    to_deploy_alias = "A_Deployer"
    mlflow.set_experiment("Projet_MlOps")

    artifact_path = "train_for_prod"

    # Retrouve la version à déployer
    to_deploy_model_version = get_modelversion_by_alias(
        client, model_name, to_deploy_alias
    )
    print(
        f"L'alias '{to_deploy_alias}' pointe actuellement vers la version {to_deploy_model_version.version}"
    )

    # Passe "En production"
    client.set_registered_model_alias(
        model_name, production_alias, to_deploy_model_version.version
    )
    print(
        f"L'alias '{production_alias}' est maintenant défini pour la version {to_deploy_model_version.version}"
    )

    # Supprime l'ancien alias A_Deployer
    client.delete_registered_model_alias(model_name, to_deploy_alias)
    print(f"L'alias '{to_deploy_alias}' a été supprimé")

    return to_deploy_model_version.version

if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    # project_dir = Path(__file__).resolve().parents[2]
    set_production_alias(False)
