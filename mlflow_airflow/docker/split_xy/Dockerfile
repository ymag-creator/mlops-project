FROM python:3.13-slim

WORKDIR /app

# RUN mkdir -p data/to_ingest/silver

COPY ./split_xy.py ./split_xy.py
COPY ./utils.py ./utils.py

COPY ./requirements.txt ./requirements.txt

RUN pip install -r requirements.txt
