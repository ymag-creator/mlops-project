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

HOST_OS= os.getenv("HOST_OS")

# def test():
#     # Chemin du répertoire à inspecter
#     repertoire = "data/raw_to_ingest"
#     # Lister les fichiers uniquement (sans les dossiers)
#     fichiers = [
#         f for f in os.listdir(repertoire) if os.path.isfile(os.path.join(repertoire, f))
#     ]
#     print("Fichiers dans le répertoire :", fichiers)

with DAG(
    dag_id="train_with_new_data",
    tags=["Projet MLOps"],
    default_args={
        "owner": "airflow",
        "start_date": datetime(2025, 1, 4),  # days_ago(0, minute=1),
    },
    schedule_interval="0 12 * * *",  # "*/2 * * * *",
    catchup=False,
) as dag:

    def ensure_folder(folder_path):
        """ Create folder if necessary"""
        if os.path.exists(folder_path) == False :
            os.makedirs(folder_path, exist_ok=True)

    def create_dir():
        ensure_folder("/opt/airflow/data/raw_ingested")
        ensure_folder("/opt/airflow/data/raw_to_ingest")
        ensure_folder("/opt/airflow/data/processed_to_train")
        ensure_folder("/opt/airflow/data/processed_trained")
        ensure_folder("/opt/airflow/data/model")

    task_create_dir = PythonOperator(task_id="create_dirs", python_callable=create_dir)

    def reinit_raw_to_ingest():
        file_to_delete = "/opt/airflow/data/raw_ingested/accidents.csv"
        if os.path.exists(file_to_delete):
            os.remove(file_to_delete)
            print(f"Fichier supprimé : {file_to_delete}")
        else:
            print(f"Fichier non trouvé : {file_to_delete}")

        src_dir = "/opt/airflow/data/raw_ingested"
        dst_dir = "/opt/airflow/data/raw_to_ingest"

        for filename in os.listdir(src_dir):
            src_path = os.path.join(src_dir, filename)
            dst_path = os.path.join(dst_dir, filename)
            if os.path.isfile(src_path):
                shutil.move(src_path, dst_path)
                print(f"Fichier déplacé : {filename}")

    task_reinit_raw_to_ingest = PythonOperator(
        task_id="reinit_raw_to_ingest", python_callable=reinit_raw_to_ingest
    )

    # def block():
    #     raise Exception("ee")
    # task_block = PythonOperator(task_id="block", python_callable=block)

    # Variable.set(
    #     key="cities", value=json.dumps(["paris", "london", "washington"])
    # )

    # task_test = PythonOperator(
    #         task_id="test",
    #         python_callable=test)

    # ---------------- Vérification de nouveaux fichiers à traiter ----------------
    fs_defaut_conn_task = get_fs_defaut_conn_task(dag)

    raw_sensor = FileSensor(
        task_id="raw_sensor",
        filepath="data/raw_to_ingest/*",
        poke_interval=5,
        timeout=11,
        mode="poke",
    )

    # ---------------- build les images Docker ----------------
    PROJECTMLOPS_PATH = os.getenv("PROJECTMLOPS_PATH")
    build_command = ""

    if HOST_OS=="LINUX":
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
            task_id="build_docker_etl",
            bash_command=build_command.format(path_name="etl", name="projectmlops_etl")
                
        )
        build_docker_image_split = BashOperator(
            task_id="build_docker_split",
            bash_command=build_command.format(path_name="split_xy", name="projectmlops_splitxy")
        )
        build_docker_image_train = BashOperator(
            task_id="build_docker_train",
            bash_command=build_command.format(path_name="train", name="projectmlops_train")
        )
        build_docker_image_mlflow = BashOperator(
            task_id="build_docker_mlflow",
            bash_command=build_command.format(path_name="mlflow", name="projectmlops_mlflow")
        )
        build_docker_image_server_test = BashOperator(
            task_id="build_docker_server_test",
            bash_command=build_command.format(
                path_name="server_test", name="projectmlops_server_test"
            ),
        )
        build_docker_image_server_deploy = BashOperator(
            task_id="build_docker_server_deploy",
            bash_command=build_command.format(
                path_name="server_deploy", name="projectmlops_server_deploy"
            ),
        )

    # ---------------- ETL ----------------
    if HOST_OS=="LINUX":
        docker_url="unix:///var/run/docker.sock"
    else:
        docker_url="tcp://host.docker.internal:2375"

    etl_task = DockerOperator(
        task_id="etl",
        image="projectmlops_etl:latest",
        docker_url=docker_url,
        network_mode="bridge",
        auto_remove="force",
        command="python3 etl.py",
        mounts=[
            Mount(
                # source="/home/ubuntu/airflow/data/to_ingest",
                source=PROJECTMLOPS_PATH + "/data/raw_to_ingest",
                #source="/Users/ymagnac/Desktop/Projets/Projet_MLOps_accidents/data/raw_to_ingest", # ajout YM
                # source=os.getenv("APP_DATA_LOCALHOST_DIR") + "/to_ingest", # permet de ne pas mettre le chemin en dur
                target="/app/data/raw_to_ingest",
                type="bind",
            ),
            Mount(
                # source="/home/ubuntu/airflow/data/to_ingest",
                source=PROJECTMLOPS_PATH + "/data/raw_ingested",
                #source="/Users/ymagnac/Desktop/Projets/Projet_MLOps_accidents/data/raw_ingested", # ajout YM
                target="/app/data/raw_ingested",
                type="bind",
            ),
        ],
    )

    # ---------------- Split Xy ----------------
    splitxy_task = DockerOperator(
        task_id="split_xy",
        image="projectmlops_splitxy:latest",
        docker_url=docker_url,
        network_mode="bridge",
        auto_remove="force",
        command="python3 split_xy.py",
        mounts=[
            Mount(
                # source="/home/ubuntu/airflow/data/to_ingest",
                source=PROJECTMLOPS_PATH + "/data/raw_ingested",
                #source="/Users/ymagnac/Desktop/Projets/Projet_MLOps_accidents/data/raw_ingested", # ajout YM
                # source=os.getenv("APP_DATA_LOCALHOST_DIR") + "/to_ingest", # permet de ne pas mettre le chemin en dur
                target="/app/data/raw_ingested",
                type="bind",
            ),
            Mount(
                # source="/home/ubuntu/airflow/data/to_ingest",
                source=PROJECTMLOPS_PATH + "/data/processed_to_train",
                target="/app/data/processed_to_train",
                type="bind",
            ),
        ],
    )

    # ---------------- train ----------------
    train_task = DockerOperator(
        task_id="train",
        image="projectmlops_train:latest",
        docker_url=docker_url,
        network_mode="bridge",
        auto_remove="force",
        command="python3 train.py",
        mounts=[
            Mount(
                # source="/home/ubuntu/airflow/data/to_ingest",
                source=PROJECTMLOPS_PATH + "/data/processed_to_train",
                # source=os.getenv("APP_DATA_LOCALHOST_DIR") + "/to_ingest", # permet de ne pas mettre le chemin en dur
                target="/app/data/processed_to_train",
                type="bind",
            ),
            Mount(
                # source="/home/ubuntu/airflow/data/to_ingest",
                source=PROJECTMLOPS_PATH + "/data/processed_trained",
                target="/app/data/processed_trained",
                type="bind",
            ),
            Mount(
                # source="/home/ubuntu/airflow/data/to_ingest",
                source=PROJECTMLOPS_PATH + "/data/model",
                target="/app/data/model",
                type="bind",
            ),
        ],
    )

    # ---------------- MlFlow ----------------
    # from docker.types import NetworkingConfig, EndpointConfig
    # networking_config = NetworkingConfig(
    #     {"mlflow_airflow_mlflow_airflow_net": EndpointConfig(version="2",ipv4_address="172.25.0.90")}
    # )
    mlflow_task = DockerOperator(
        task_id="mlflow",
        image="projectmlops_mlflow:latest",
        docker_url=docker_url,
        network_mode="mlflow_airflow_mlflow_airflow_net",
        auto_remove="force",
        command="python3 mlflow_push.py",
        # container_config={
        #     "networking_config": networking_config
        # },
        mounts=[
            Mount(
                # source="/home/ubuntu/airflow/data/to_ingest",
                source=PROJECTMLOPS_PATH + "/data/processed_trained",
                target="/app/data/processed_trained",
                type="bind",
            ),
            Mount(
                # source="/home/ubuntu/airflow/data/to_ingest",
                source=PROJECTMLOPS_PATH + "/data/model",
                target="/app/data/model",
                type="bind",
            ),
        ],
    )

    # ---------------- dagshub ----------------
    server_test_task = DockerOperator(
        task_id="server_test",
        image="projectmlops_server_test:latest",
        docker_url=docker_url,
        network_mode="bridge",
        auto_remove="force",
        command="python3 server_test.py",
        mounts=[
            Mount(
                source=PROJECTMLOPS_PATH + "/mlflow_airflow/kube/.kube",
                target="/root/.kube",
                type="bind",
                read_only=True,
            ),
            Mount(
                source=PROJECTMLOPS_PATH + "/mlflow_airflow/kube/docker/data_test",
                target="/app/data",
                type="bind",
            ),
        ],
    )

    server_deploy_task = DockerOperator(
        task_id="server_deploy",
        image="projectmlops_server_deploy:latest",
        docker_url=docker_url,
        network_mode="mlflow_airflow_mlflow_airflow_net",
        auto_remove="force",
        command="python3 server_deploy.py",
        mounts=[
            Mount(
                source=PROJECTMLOPS_PATH + "/mlflow_airflow/kube/.kube",
                target="/root/.kube",
                type="bind",
                read_only=True,
            ),
            Mount(
                source=PROJECTMLOPS_PATH + "/mlflow_airflow/kube/docker/data_server",
                target="/app/data",
                type="bind",
            ),
            Mount(
                source=PROJECTMLOPS_PATH + "/data",
                target="/app/data_to_push",
                type="bind",
                read_only=True,
            ),
        ],
    )

    task_create_dir >> task_reinit_raw_to_ingest >> fs_defaut_conn_task
    fs_defaut_conn_task >> raw_sensor
    raw_sensor >> group_build_docker_image >> etl_task >> splitxy_task >> train_task >> mlflow_task
    mlflow_task >> server_test_task >> server_deploy_task
