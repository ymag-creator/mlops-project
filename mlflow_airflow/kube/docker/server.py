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
import pandas as pd
from typing import List

app = FastAPI()

def load_model():
    print("Load model")
    model, scaler = load_model_from_mlflow(True)
    if not model:
        raise ValueError("Impossible de charger le model")
    if not scaler:
        raise ValueError("Impossible de charger le scaler")
    print(model, scaler)
    return model, scaler


model, scaler = load_model()


# ------------------------ variable environnement ---------------------------------------
# MYSQL_ROOT_PASSWORD = os.getenv("MYSQL_ROOT_PASSWORD")
# MYSQL_USER = os.getenv("MYSQL_USER")
# MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
# MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

# print(MYSQL_ROOT_PASSWORD, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE)

# mysql_user = MYSQL_USER  # "Davy"
# mysql_password = MYSQL_PASSWORD  # "Davy123!"
# mysql_host = "mysql-port"
# mysql_port = "3307"
# mysql_database = MYSQL_DATABASE  # "ZXZhbF9teXNxbF9kYg=="


MLFLOW_URL = os.environ.get("MLFLOW_URL", "http://host.docker.internal:5000")

# print(os.environ)

# ------------------------ Authentification ---------------------------------------
pwd_context = CryptContext(schemes=["sha256_crypt"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Configuration pour le JWT
SECRET_KEY = "PrOJet_MlOpS"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRATION = 30

users_db = {
    "Test": {
        "username": "Test",
        "name": "Test",
        "hashed_password": pwd_context.hash("passW0rd_test_01"),
    },
    "api_streamlit": {
        "username": "api streamlit",
        "name": "api streamlit",
        "hashed_password": pwd_context.hash("passW0rd_StrEAMlIT"),
    },
}

# ------------------------ schema ---------------------------------------


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class DataAccident(BaseModel):
    # table_name: str
    # columns: dict
    place: float
    catu: float
    sexe: float
    secu1: float
    year_acc: float
    victim_age: float
    catv: float
    obsm: float
    motor: float
    catr: float
    circ: float
    surf: float
    situ: float
    vma: float
    jour: float
    mois: float
    lum: float
    dep: float
    com: float
    agg_: float
    int: float
    atm: float
    col: float
    lat: float
    long: float
    hour: float
    nb_victim: float
    nb_vehicules: float

class DataAccidents(BaseModel):
    data: List[DataAccident]

class Predictions(BaseModel):
    predictions: List[int]


print("ready")


# ------------------------ Méthodes ---------------------------------------
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=15)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = users_db.get(username, None)
    if user is None:
        raise credentials_exception
    return user


# ------------------------ Charge le model ---------------------------------------
# def load_model():
#     # model = joblib.load()
#     # scaler = joblib.load("/home/bentoml/bento/src/scaler.pkl")
#     pass


# ------------------------ Rest API ---------------------------------------
@app.get("/status")
def version():
    """
    Description:
    Cette route renvoie un message "Hello World!".
    """
    return {"Version": "1.0"}


@app.post("/token", response_model=Token)
async def token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Description:
    Cette route permet à un utilisateur de s'authentifier en fournissant un nom d'utilisateur et un mot de passe. Si l'authentification est réussie, elle renvoie un jeton d'accès JWT.

    Args:
    - form_data (OAuth2PasswordRequestForm, dépendance): Les données de formulaire contenant le nom d'utilisateur et le mot de passe.

    Returns:
    - Token: Un modèle de jeton d'accès JWT.

    Raises:
    - HTTPException(400, detail="Incorrect username or password"): Si l'authentification échoue en raison d'un nom d'utilisateur ou d'un mot de passe incorrect, une exception HTTP 400 Bad Request est levée.
    """
    print(form_data.username)
    print(users_db)
    user = users_db.get(form_data.username)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password 1")
    hashed_password = user.get("hashed_password")
    if not user or not verify_password(form_data.password, hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password 2")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRATION)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/validate_token")
def validate_token(current_user: str = Depends(get_current_user)):
    """
    Description:
    Cette route renvoie un message "Hello World, but secured!" uniquement si l'utilisateur est authentifié.

    Args:
    - current_user (str, dépendance): Le nom d'utilisateur de l'utilisateur actuellement authentifié.

    Returns:
    - JSON: Renvoie un JSON contenant un message de salutation sécurisé si l'utilisateur est authentifié, sinon une réponse non autorisée.

    Raises:
    - HTTPException(401, detail="Unauthorized"): Si l'utilisateur n'est pas authentifié, une exception HTTP 401 Unauthorized est levée.
    """

    return {"message": f"Hello {current_user}, but secured!"}


@app.post("/predict", response_model=Predictions)
def predict(data_accident: DataAccidents, current_user: str = Depends(get_current_user)):
# def predict(data_accident: DataAccidents):
    if not model:
        raise ValueError("Model non chargé")
    if not scaler:
        raise ValueError("Scaler non chargé")
    print("------")
    print(data_accident)
    print("------")
    print(data_accident.model_dump())
    df = pd.DataFrame(data_accident.model_dump()["data"])
    print("------")
    print(df.head())

    numerical_cols = df.select_dtypes(include=["int", "float"]).columns
    df[numerical_cols] = scaler.transform(df[numerical_cols])
    print("------", df.head())
    pred = model.predict(df)
    print("prédiction", pred)
    return {"predictions": pred}

    # request = ctx.request
    # user = request.state.user if hasattr(request.state, "user") else None
    # # Convert the input data to a numpy array
    # input_series = np.array(
    #     [
    #         input_data.GRE_Score,
    #         input_data.TOEFL_Score,
    #         input_data.University_Rating,
    #         input_data.SOP,
    #         input_data.LOR,
    #         input_data.CGPA,
    #         input_data.Research,
    #     ]
    # )
    # input_series = input_series.reshape(1, -1)
    # scaler = joblib.load("/home/bentoml/bento/src/scaler.pkl")
    # # scaler = joblib.load("/home/bentoml/bento/src/src/scaler.pkl")
    # # scaler = joblib.load("scaler.pkl")
    # print(scaler)
    # print(input_series)
    # input_series = scaler.transform(input_series)
    # print(input_series)
    # result = self.model.predict(input_series)
    # return {"prediction": result.tolist(), "user": user}
    # return {"message": f"Hello {current_user}, predict"}
