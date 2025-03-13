FROM python:3.13-slim

WORKDIR /app

# RUN mkdir -p data/to_ingest/silver

COPY ./etl.py ./etl.py
COPY ./check_structure.py ./check_structure.py

COPY ./requirements.txt ./requirements.txt

RUN pip install -r requirements.txt
