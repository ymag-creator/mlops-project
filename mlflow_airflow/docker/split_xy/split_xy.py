# -*- coding: utf-8 -*-
import pandas as pd
import logging
from sklearn.model_selection import train_test_split
from check_structure import ensure_folder
import os
import sys

def split_xy(data_dir=None):
    """Runs data processing scripts to turn raw data from (../raw) into
    cleaned data ready to be analyzed (saved in ../preprocessed).
    """
    # répertoire data à utiliser
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    elif data_dir == None:
        data_dir = "data"

    input_dir = os.path.join(data_dir, "raw_ingested")
    output_dir = os.path.join(data_dir, "processed_to_train")

    logger = logging.getLogger(__name__)
    logger.info("making final data set from raw data")

    input_filepath_df = os.path.join(input_dir, "usagers-2021.csv")

    # Call the main data processing function with the provided file paths
    process_data(
        input_filepath_df,
        input_dir,
        output_dir,
    )


def process_data(
    input_filepath_df,
    input_dir,
    output_dir,
):
    # --Importing dataset
    df = pd.read_csv(input_filepath_df, sep=";")

    target = df["grav"]
    feats = df.drop(["grav"], axis=1)

    X_train, X_test, y_train, y_test = train_test_split(
        feats, target, test_size=0.3, random_state=42
    )

    ensure_folder(output_dir)
    # --Saving the dataframes to their respective output file paths
    for file, filename in zip(
        [X_train, X_test, y_train, y_test], ["X_train", "X_test", "y_train", "y_test"]
    ):
        output_filepath = os.path.join(output_dir, f"{filename}.csv")
        file.to_csv(output_filepath, index=False)


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    # project_dir = Path(__file__).resolve().parents[2]

    split_xy()
