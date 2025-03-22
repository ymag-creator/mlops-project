import os
from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.sensors.filesystem import FileSensor
from airflow.operators.docker_operator import DockerOperator
from docker.types import Mount
from airflow.utils.task_group import TaskGroup
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.models import Variable
from datetime import datetime
from get_fs_defaut_conn_task import get_fs_defaut_conn_task
import shutil

HOST_OS = os.getenv("HOST_OS")

# def test():
#     # Chemin du répertoire à inspecter
#     repertoire = "data/raw_to_ingest"
#     # Lister les fichiers uniquement (sans les dossiers)
#     fichiers = [
#         f for f in os.listdir(repertoire) if os.path.isfile(os.path.join(repertoire, f))
#     ]
#     print("Fichiers dans le répertoire :", fichiers)

with DAG(
    dag_id="kub_test",
    tags=["Projet MLOps"],
    default_args={
        "owner": "airflow",
        "start_date": datetime(2025, 3, 4),  # days_ago(0, minute=1),
    },
    schedule_interval="* 1 * * *",  # "*/2 * * * *",
    catchup=False,
) as dag:

    # ---------------- build les images Docker ----------------
    PROJECTMLOPS_PATH = os.getenv("PROJECTMLOPS_PATH")
    build_command = ""

    if HOST_OS == "LINUX":
        build_command = """
                        export DOCKER_HOST=unix:///var/run/docker.sock
                        cd "/opt/airflow/docker/{path_name}/" && docker build -t {name}:latest .
                """
    else:
        build_command = """
                export DOCKER_HOST=tcp://host.docker.internal:2375
                cd "/opt/airflow/docker/{path_name}/" && docker build -t {name}:latest .
                """

    with TaskGroup("build_docker") as group_build_docker_image:
        build_docker_image_etl = BashOperator(
            task_id="build_docker_kubtest",
            bash_command=build_command.format(
                path_name="kub_test", name="projectmlops_kubtest"
            ),
        )

    # ---------------- Test kubernestes ----------------
    if HOST_OS == "LINUX":
        docker_url = "unix:///var/run/docker.sock"
    else:
        docker_url = "tcp://host.docker.internal:2375"

    kub_task = DockerOperator(
        task_id="etl",
        image="projectmlops_kubtest:latest",
        docker_url=docker_url,
        network_mode="bridge",
        auto_remove="force",
        command="python3 testkub.py",
        mounts=[
            Mount(
                source=PROJECTMLOPS_PATH + "/mlflow_airflow/kube/.kube",
                target="/root/.kube",
                type="bind",
                read_only=True,
            ),
            Mount(
                source=PROJECTMLOPS_PATH + "/mlflow_airflow/kube/docker/data_test",
                target="/app/data_test",
                type="bind",
                read_only=True,
            ),
        ],
    )

    group_build_docker_image >> kub_task
