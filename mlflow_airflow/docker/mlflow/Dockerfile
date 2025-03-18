FROM python:3.13-slim

WORKDIR /app

# RUN mkdir -p data/to_ingest/silver

COPY ./mlflow_push.py ./mlflow_push.py

COPY ./requirements.txt ./requirements.txt

RUN pip install -r requirements.txt
