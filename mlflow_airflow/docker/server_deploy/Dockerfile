FROM python:3.13-slim

WORKDIR /app

# RUN mkdir -p data/to_ingest/silver

COPY ./server_deploy.py ./server_deploy.py
COPY ./mlflow_utils.py ./mlflow_utils.py

COPY ./requirements.txt ./requirements.txt

RUN pip install -r requirements.txt