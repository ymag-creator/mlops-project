FROM python:3.13-slim

WORKDIR /app

# RUN mkdir -p data/to_ingest/silver

COPY ./server_test.py ./server_test.py

COPY ./requirements.txt ./requirements.txt

RUN pip install -r requirements.txt