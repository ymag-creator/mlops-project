# -*- coding: utf-8 -*-
import pandas as pd
import logging
import os
import sys
from sklearn import ensemble
import joblib
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from utils import ensure_folder, move_files, delete_files


def train(data_dir=None):
    """Runs data processing scripts to turn raw data from (../raw) into
    cleaned data ready to be analyzed (saved in ../preprocessed).
    """
    # répertoire data à utiliser
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    elif data_dir == None:
        data_dir = "data"

    input_dir = os.path.join(data_dir, "processed_to_train")
    output_data_dir = os.path.join(data_dir, "processed_trained")
    output_model_dir = os.path.join(data_dir, "model")

    logger = logging.getLogger(__name__)
    logger.info("Train")

    input_filepath_X_train = os.path.join(input_dir, "X_train.csv")
    input_filepath_X_test = os.path.join(input_dir, "X_test.csv")
    input_filepath_y_train = os.path.join(input_dir, "y_train.csv")
    input_filepath_y_test = os.path.join(input_dir, "y_test.csv")

    # Call the main data processing function with the provided file paths
    process_train(
        input_filepath_X_train,
        input_filepath_X_test,
        input_filepath_y_train,
        input_filepath_y_test,
        input_dir,
        output_data_dir,
        output_model_dir,
    )


def normalize_X(X_train, X_test, output_dir):
    print(X_train.info())
    numerical_cols = X_train.select_dtypes(include=["int", "float"]).columns
    scaler = MinMaxScaler()
    X_train[numerical_cols] = scaler.fit_transform(X_train[numerical_cols])
    X_test[numerical_cols] = scaler.transform(X_test[numerical_cols])
    print(X_train.head())
    joblib.dump(scaler, os.path.join(output_dir, "scaler.pkl"))
    # print(X_train.head())
    # print(X_test.head())
    return X_train, X_test


def process_train(
    input_filepath_X_train,
    input_filepath_X_test,
    input_filepath_y_train,
    input_filepath_y_test,
    input_dir,
    output_data_dir,
    output_model_dir,
):
    # --Importing dataset
    print(joblib.__version__)

    print(output_data_dir)
    print(output_model_dir)
    ensure_folder(output_data_dir)
    delete_files(output_data_dir)
    ensure_folder(output_model_dir)
    delete_files(output_model_dir)

    X_train = pd.read_csv(input_filepath_X_train, sep=";")
    X_test = pd.read_csv(input_filepath_X_test, sep=";")
    y_train = pd.read_csv(input_filepath_y_train, sep=";")
    y_test = pd.read_csv(input_filepath_y_test, sep=";")
    # Nomalize les données
    X_train, X_test = normalize_X(X_train, X_test, output_model_dir)

    y_train = np.ravel(y_train)
    y_test = np.ravel(y_test)

    rf_classifier = ensemble.RandomForestClassifier(n_jobs=-1)

    # --Train the model
    rf_classifier.fit(X_train, y_train)
    print(rf_classifier.score(X_train, y_train))
    print(rf_classifier.score(X_test, y_test))

    # --Save the trained model to a file
    joblib.dump(rf_classifier, os.path.join(output_model_dir, "trained_model.pkl"))

    print("Model trained and saved successfully.")

    # Déplace les fichers dans processed_trained
    move_files(input_dir, output_data_dir)


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    # project_dir = Path(__file__).resolve().parents[2]

    train()
