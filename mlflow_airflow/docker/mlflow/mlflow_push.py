# -*- coding: utf-8 -*-
import pandas as pd
import logging
import os
import sys
import joblib
import numpy as np
# from sklearn.metrics import (
#     accuracy_score,
#     root_mean_squared_error,
#     mean_absolute_error,
#     r2_score,
# )
from sklearn.metrics import classification_report, accuracy_score, f1_score

from mlflow import MlflowClient
import mlflow
from datetime import datetime, timezone


def mlflow_push(data_dir=None, in_container=True):
    """Runs data processing scripts to turn raw data from (../raw) into
    cleaned data ready to be analyzed (saved in ../preprocessed).
    """
    # répertoire data à utiliser
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
        in_container = sys.argv[2]
    elif data_dir == None:
        data_dir = "data"

    input_dir = os.path.join(data_dir, "processed_trained")
    model_dir = os.path.join(data_dir, "model")

    logger = logging.getLogger(__name__)
    logger.info("mlflow_push")

    input_filepath_X_train = os.path.join(input_dir, "X_train.csv")
    input_filepath_X_test = os.path.join(input_dir, "X_test.csv")
    input_filepath_y_train = os.path.join(input_dir, "y_train.csv")
    input_filepath_y_test = os.path.join(input_dir, "y_test.csv")

    # Call the main data processing function with the provided file paths
    process_mlflow(
        in_container,
        input_filepath_X_train,
        input_filepath_X_test,
        input_filepath_y_train,
        input_filepath_y_test,
        model_dir,
    )


def normalize_X(X_train, X_test, model_dir):
    # print(X_train.info())
    numerical_cols = X_train.select_dtypes(include=["int", "float"]).columns
    scaler = joblib.load(os.path.join(model_dir, "scaler.pkl"))
    X_train[numerical_cols] = scaler.transform(X_train[numerical_cols])
    X_test[numerical_cols] = scaler.transform(X_test[numerical_cols])
    # print(X_train.head())
    # print(X_test.head())
    return X_train, X_test


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


def process_mlflow(
    in_container,
    input_filepath_X_train,
    input_filepath_X_test,
    input_filepath_y_train,
    input_filepath_y_test,
    model_dir,
):
    print("in_container", in_container)

    X_train = pd.read_csv(input_filepath_X_train, sep=";")
    X_test = pd.read_csv(input_filepath_X_test, sep=";")
    y_train = pd.read_csv(input_filepath_y_train, sep=";")
    y_test = pd.read_csv(input_filepath_y_test, sep=";")
    # Nomalize les données
    X_train, X_test = normalize_X(X_train, X_test, model_dir)

    y_train = np.ravel(y_train)
    y_test = np.ravel(y_test)

    rf_classifier = joblib.load(os.path.join(model_dir, "trained_model.pkl"))

    # -- Prediction
    y_train_pred = rf_classifier.predict(X_train)
    y_test_pred = rf_classifier.predict(X_test)

    # Scores
    # # RMSE
    # rmse_train = root_mean_squared_error(y_train, y_train_pred)
    # print(f"RMSE train : {rmse_train}")
    # rmse_test = root_mean_squared_error(y_test, y_test_pred)
    # print(f"RMSE test : {rmse_test}")
    # # MAE
    # mae_train = mean_absolute_error(y_train, y_train_pred)
    # print(f"MAE train : {mae_train}")
    # mae_test = mean_absolute_error(y_test, y_test_pred)
    # print(f"MAE test : {mae_test}")
    # # Accuracy
    # accuracy_train = accuracy_score(y_train, y_train_pred)
    # print(f"Accuracy train : {accuracy_train}")
    # accuracy_test = accuracy_score(y_test, y_test_pred)
    # print(f"Accuracy test : {accuracy_test}")
    # # R²
    # r2_train = r2_score(y_train, y_train_pred)
    # print(f"R² train : {r2_train}")
    # r2_test = r2_score(y_test, y_test_pred)
    # print(f"R² test : {r2_test}")

    # accuracy
    accuracy_train = accuracy_score(y_train, y_train_pred)
    print(f"Accuracy train: {accuracy_train}")
    accuracy_test = accuracy_score(y_test, y_test_pred)
    print(f"Accuracy test : {accuracy_test}")
    # train et test score
    f1_score_train = f1_score(y_train, y_train_pred, average="weighted")
    print(f"F1 score train : {f1_score_train}")
    f1_score_test = f1_score(y_test, y_test_pred, average="weighted")
    print(f"F1 Score test : {f1_score_test}")
    # Rapport détaillé
    detailled_report = classification_report(y_test, y_test_pred)
    print(f"Classification report :\n {detailled_report}")
    # Matrice de confusion
    ct = pd.crosstab(
        y_test, y_test_pred,
        rownames=["Classe réelle"],
        colnames=["Classe prédite"],
    )

    # récupère la dernière expérience en prod
    if in_container == True:
        server_adress = "http://mlflow-server:5000"  # "http://172.25.0.100:5000"
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
    # -- envoi à MlFlow
    run_name = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    artifact_path = "train_for_prod"

    metrics = {
        "accuracy_train": accuracy_train,
        "accuracy test": accuracy_test,
        "f1_score_train": f1_score_train,
        "f1_score_test": f1_score_test,
        # "classification_report": detailled_report,
        # "prédiction": ct,
    }

    with mlflow.start_run(
        run_name=run_name, tags={"Stage": "AA", "Model": "RandomForestClassifier"}
    ) as run:
        mlflow.log_params(rf_classifier.get_params())
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(
            sk_model=rf_classifier, input_example=X_train, artifact_path=artifact_path
        )
        mlflow.log_artifact(os.path.join(model_dir, "scaler.pkl"))
        activerun_id = run.info.run_id
        print("Active run id", activerun_id, run.info.experiment_id, run.info.status)

    # Retrouve la dernière version en prod et l'experience correspondante
    model_version = get_modelversion_by_alias(client, model_name, production_alias)
    # vérifie avec le dernier model du repo la variation du score
    if model_version:
        run = mlflow.get_run(model_version.run_id)
        current_prod_f1_score_test = run.data.metrics["f1_score_test"]
        print(" Model en prod --------------------")
        print(current_prod_f1_score_test)
        tag_validation = "F1_Validation"
        # si delta de score supérieur à 1%, monte une erreur
        if abs((current_prod_f1_score_test - f1_score_test) / current_prod_f1_score_test * 100) > 1:
            client.set_tag(run_id=activerun_id, key=tag_validation, value="Error")
            raise Exception("Alerte le modèle dévie de plsu de 1%")
        else:
            client.set_tag(run_id=activerun_id, key=tag_validation, value="Ok")
    else:
        print(" pas de Model en prod --------------------")

    # Si on est là c'est qui'il n'y a pas de version en prod ou pas d'écart significatif de rmse, passe le run en prod
    # Enregistre le run comme version du model
    result = mlflow.register_model(
        f"runs:/{activerun_id}/{artifact_path}",
        model_name,
    )
    # Set l'alias A déployer
    client.set_registered_model_alias(model_name, to_deploy__alias, result.version)
    # Set le tag
    client.set_model_version_tag(
        model_name,
        str(result.version),
        "validation_status",
        "approved",
    )
    client.set_model_version_tag(
        model_name,
        str(result.version),
        "Model",
        "RandomForestClassifier",
    )

if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    # project_dir = Path(__file__).resolve().parents[2]
    mlflow_push()
