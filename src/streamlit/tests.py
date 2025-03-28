import requests
import time
import pandas as pd
import numpy as np
from sklearn.metrics import classification_report, accuracy_score, f1_score
from pytest import approx
import os
import random


# The URL of the login and prediction endpoints
server_uri = "http://127.0.0.1:31234"
token_url = server_uri + "/token"
validate_token_url = server_uri + "/validate_token"
predict_url = server_uri + "/predict"

# Données de connexion
bad_credentials = {
    "username": "user123",
    "password": "password123",
    "grant_type": "password",
}
good_credentials = {
    "username": "Test",
    "password": "passW0rd_test_01",
    "grant_type": "password",
}

X_test = None

# columns = ["place","catu","sexe","secu1","year_acc","victim_age","catv","obsm","motor","catr","circ","surf","situ","vma","jour","mois","lum","dep","com","agg_","int",
#     "atm","col","lat","long","hour","nb_victim","nb_vehicules"]
# data_to_test = [
#     [[1,1,2,1.0,2021,34.0,2.0,2.0,1.0,3,1.0,1.0,1.0,50.0,16,3,1,94,94069,2,2,0.0,3.0,48.81723,2.4588,9,2,2], 0],
#     [[1,1,1,2.0,2021,47.0,1.0,2.0,1.0,4,1.0,2.0,1.0,50.0,15,1,1,93,93007,2,9,0.0,3.0,48.9381112755,2.4712868984,11,2,2], 0],
#     [[1,1,1,1.0,2021,24.0,2.0,0.0,1.0,4,2.0,1.0,1.0,30.0,28,10,5,75,75115,2,3,0.0,6.0,48.847365,2.278937,0,1,1], 0],
#     [[2,2,2,1.0,2021,18.0,2.0,2.0,1.0,3,2.0,1.0,1.0,90.0,29,5,1,34,34130,1,1,0.0,5.0,43.501406,3.189297,12,9,4], 1],
#     [[1,1,1,0.0,2021,21.0,1.0,2.0,5.0,3,2.0,1.0,1.0,90.0,25,10,3,12,12176,1,1,0.0,2.0,44.39666,2.5071,20,2,2],1]
# ]

def check_server():
    # test le démarage du serveur 5 secondes, car Uvicorn met un peu de temps à démarrer
    seconds = 0
    while seconds < 5:
        # check la status connexion
        try:
            r = requests.get(url=server_uri + "/status")
            # print(r, r.status_code)
            break
        except:
            seconds += 1
            time.sleep(1)
            # print("seconds", seconds)

    token = ""


def test_token():

    # Test login incorrect
    login_response = requests.post(
        token_url,
        data=bad_credentials,
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    text = [f"Test login incorrect {login_response}"]

    # Test login correct
    login_response = requests.post(
        token_url,
        data=good_credentials,
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    text.append(f"Test login correct {login_response}")
    global token 
    token = login_response.json()["access_token"]
    return text

def test_validate_token():
    # Test login incorrect
    response = requests.get(
        validate_token_url,
        headers={
            # "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiZGFuaWVsIiwiZXhwaXJlcyI6MTc0MDUwMTczNC42MzM5MDk1fQ.AAnoXyPEn97skuDQL0HRMrxtIuTftBTjYoWLJAPMeYE"
            "Authorization": "Bearer "
            + "totototototototototototototototototototototototototototo"
        },
    )
    text = [f"Test token incorrect {response}"]

    # Test login correct
    response = requests.get(        
        validate_token_url,
        headers={
            # "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiZGFuaWVsIiwiZXhwaXJlcyI6MTc0MDUwMTczNC42MzM5MDk1fQ.AAnoXyPEn97skuDQL0HRMrxtIuTftBTjYoWLJAPMeYE"
            "Authorization": "Bearer "
            + token
        },
    )
    text.append(f"Test token correct {response}")
    return text

def read_data(dir):
    global X_test
    X_test = pd.read_csv(os.path.join(dir, "X_test.csv"), sep=";")


def test_prediction():
    # Test erreur sans token
    # response = requests.post(
    #     predict_url,
    #     headers={
    #         "Authorization": "Bearer " + "totototototototototototototototototototototototototototo"
    #     },
    # )
    # text = [f"Test token incorrect {response}"]

    if X_test is None:
        raise ValueError("X_test est None")

    # prend de entre 1 et 300 lignes aléatoires
    n = random.randint(1, 100)
    # Extraction aléatoire
    df_sample = X_test.sample(n=n)
    print(len(df_sample))
    data_dict = df_sample.to_dict(orient="records")
    # Send a POST request to the prediction
    response = requests.post(
        predict_url,
        headers={"Authorization": "Bearer " + token},
        json={"data": data_dict},
    )
    text = [f"----Réponse de l'API de prédiction: {response.status_code}"]
    
    return text
