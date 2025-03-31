<img src="https://datascientest.com/wp-content/uploads/2022/03/logo-2021.png">

# Projet - Gravité des accidents routier en France

## Énoncé du sujet:
Une équipe de Data Scientist a développé un modèle de Machine Learning afin de prédire la gravité d'un accident routier en France. Ce modèle est destiné à être utilisé par les policiers, le SAMU et les pompiers afin de réagir plus rapidelent grâce à une meilleur priorisation des urgences.
La disponibilité et le maintien en condition opérationnelle du modèle est donc vital.
De plus, une dérive du modèle aurait des conséquences catastrophiques pour les utilisateurs et la vie des accidentés. En effet, l’évolution des données (nouvelles technologies dans les moyens de transport, nouvelles infrastructures routières, etc…) peut faire dériver le modèle. La mise à jour et le suivi des versions doivent donc être facilités.

C'est pour ces raisons que nous avons travaillé sur une architecture MLOps afin de mettre en production ce modèle, de le maintenir opérationnel en toute situation et de prévenir les pannes techniques grâce au monitoring. Enfin, notre architecture permet un ré-entraînement régulier et une détection de la dérive automatique afin de mettre en alerte les équipes techniques.


## Technologies utilisés:

*Mise en place de l’Environnement:* **Docker**  
*Automatisation de l'ingestion de données et ré-entraînement du modèle:* **AirFlow**  
*Versioning des modèles/données:* **MLFlow, Dagshub(avec DVC)**  
*Orchestration & Déploiement:* **Kubernetes qui héberge une API fastAPI**  
*Monitoring:* **Prometheus** (collecter les métriques) et **Grafana** (visualisation)  


## Equipe de développement

Notre équipe est constitué de : Davy ANEST, Philippe ARTIGNY, Yves MAGNAC, Antoine BAS

Mentor du projet : Sebastien SIME

## Architecture du projet

![SHIELD global architecture](/reports/figures/architecture_global.png)
<p align="center">
    <b>Figure 1.</b> Architecture gloable
</p>

## Getting started

Afin de reproduire notre projet, vous pouvez suivre les étapes ci-dessous:

### Initialisation de l'environnement:
```shell
python -m venv my_env
./my_env/Scripts/activate
pip install -r .\requirements.txt
python .\src\data\import_raw_data.py # puis renommez le dossier où sont stockés les données en raw_to_ingest
```
```text
Ainsi, l'architecture à cette étape doit être:
├── data
│   └── raw_to_ingest           <- Les fichiers .csv à ingérer doivent être ici
```
### Créer trois .env:
*./mlflow_airflow/.env*
```shell
AIRFLOW_UID=50000 #$(id -u)
nAIRFLOW_GID=0
PROJECTMLOPS_PATH="C:\...\Projet_MLOps_accidents" # -> remplacer par votre chemin local
HOST_OS="LINUX" ou "WINDOWS"
```

*./mlflow_airflow/docker/server_deploy/.env*
```shell
GIT_TOKEN=ghp_... # Demander les codes à l'équipe projet
DAGSHUB_TOKEN=44a99cea...
PERSISTENTVOLUME_HOSTPATH_PATH="/mnt/host/c/.../Projet_MLOps_accidents/mlflow_airflow/kube/docker/data_server" # -> remplacer les ... par votre chemin local en veillant à remplacer C:/ par /mnt/host/c/ 
```

*./mlflow_airflow/docker/server_test/.env*
```shell
PERSISTENTVOLUME_HOSTPATH_PATH="/mnt/host/c/.../Projet_MLOps_accidents/mlflow_airflow/kube/docker/data_test" # -> remplacer les ... par votre chemin local en veillant à remplacer C:/ par /mnt/host/c/ 
```

### Activez kubernetes dans docker desktop:</u> paramètres > Kubernetes > Enable Kubernetes
### Installer helm:
```shell
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
chmod 700 get_helm.sh
./get_helm.sh
```

### Récupérer les fichiers de config de votre kubernetes et l'insérer dans le fichier config du projet:
```shell
kubectl config view --raw > mlflow_airflow/kube/.kube/config
chmod 600 mlflow_airflow/kube/.kube/config
```

### Installer Prometheus
```shell
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install prometheus prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace --set grafana.service.type=NodePort --set promotheus.service.type=NodePort
```

### Lancer le dashboard Kubernetes:
```shell
kubectl apply -f kube_dashboard.yaml
kubectl proxy
# puis obtenir un jeton
kubectl get secret admin-user -n kubernetes-dashboard -o jsonpath="{.data.token}" | base64 -d
# puis ouvrir le dashboard
http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
```

### Construire l'image de base qui servira à lancer le déploiement du serveur:
```shell
cd mlflow_airflow/docker/server_deploy
build-base.bat
cd ../..
```

### Lancer le docker compose pour lancer les serveur Airflow et MLflow:
```shell
docker compose up airflow-init # attendre la fin du processus
docker compose up
```

### Ouvrir les dashboard Airflow et Mlflow:

Airflow : http://localhost:8080/  
MLFlow: http://localhost:5000  

**Dans Aiflow, cherchez le DAG train_with_new_data grâce au TAG Projet MLOps, puis lancez le**

### Ouvrir Prometheus et Grafana
**pour cela cherchez les ports sur lesquels ils sont accessibles:**
```shell
kubectl get svc -n monitoring
```
**Prometheus:** prometheus-kube-prometheus-prometheus -> cherchez le port sur lequel il est accessible (eg. 9090:30090/TCP : le port sera 30090)  
**Grafana:** prometheus-grafana -> cherchez le port sur lequel il est accessible  
Ouvrez les deux dashboards via localhost:\<port\>  

**Installez le dashboard sur Grafana -> Dashboard -> New -> Import -> Importez mlflow_airflow\kube\FastAPI\Accidents-Dashboard.json**

### L'API est accessible via le service kubernetes situé dans le namespace projet-mlops:
```shell
kubectl get svc -n projet-mlops
# fastapi-server-nodeport   NodePort   x.x.x.x   <none>        6300:31234/TCP   39h  --> ici accessible via localhost:31234/docs
```

### Pour simuler de l'activité sur votre API, et ainsi le visualiser sur Grafana, vous pouvez lancez notre streamlit:
```python src\streamlit\home.py```
