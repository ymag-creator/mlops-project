from fastapi import FastAPI
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from typing import Optional
import jwt
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta
import os
from pydantic import BaseModel
from mlflow_utils import load_model_from_mlflow
import uvicorn
import subprocess



def run_server_sync():
    print("🚀 Démarrage du serveur Uvicorn...")
    config = uvicorn.Config("server:app", port=6100, log_level="info", reload=True)
    server = uvicorn.Server(config)
    server.run()


def run_server_async():
    print("🚀 Démarrage du serveur Uvicorn...")
    uvicorn_proc = subprocess.Popen(
        [
            "uvicorn",
            "server:app",  # ton module FastAPI (adapter à ton projet)
            "--port",
            "6100",
            "--log-level",
            "info",
        ],
        # stdout=subprocess.PIPE,
        # stderr=subprocess.PIPE,
    )
    print("Serveur Uvicorn lancé")
    return uvicorn_proc


if __name__ == "__main__":
    run_server_sync()
