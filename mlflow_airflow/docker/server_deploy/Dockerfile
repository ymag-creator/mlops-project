# FROM python:3.13-slim

# WORKDIR /app

# RUN apt-get update && apt-get install -y git && apt-get clean

# COPY ./server_deploy.py ./server_deploy.py
# COPY ./mlflow_utils.py ./mlflow_utils.py
# COPY ./dvc_utils.py ./dvc_utils.py

# COPY ./requirements.txt ./requirements.txt

# VOLUME ["/app/repo_git"]

# RUN pip install -r requirements.txt

FROM server_deploy_base:latest

WORKDIR /app

COPY ./server_deploy.py ./server_deploy.py
COPY ./mlflow_utils.py ./mlflow_utils.py
COPY ./dvc_utils.py ./dvc_utils.py
COPY ./.env ./.env

VOLUME ["/app/repo_git"]