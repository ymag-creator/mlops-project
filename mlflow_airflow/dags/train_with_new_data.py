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
        "start_date": datetime(2025, 3, 4),  # days_ago(0, minute=1),
    },
    schedule_interval="* 1 * * *",  # "*/2 * * * *",
    catchup=False,
) as dag:

    # Variable.set(
    #     key="cities", value=json.dumps(["paris", "london", "washington"])
    # )

    # task_test = PythonOperator(
    #         task_id="test",
    #         python_callable=test)

    fs_defaut_conn_task = get_fs_defaut_conn_task(dag)

    raw_sensor = FileSensor(
        task_id="raw_sensor",
        filepath="data/raw_to_ingest/*",
        poke_interval=5,
        timeout=11,
        mode="poke",
    )

    PROJECTMLOPS_PATH = os.getenv("PROJECTMLOPS_PATH")

    with TaskGroup("build_docker") as group_build_docker_image:
        build_docker_image_etl = BashOperator(
            task_id="build_docker_etl",
            bash_command=f"""
                export DOCKER_HOST=tcp://host.docker.internal:2375
                cd "/opt/airflow/docker/etl/" && docker build -t projectmlops_etl:latest .
                """,
            # cd "{PROJECTMLOPS_PATH}/mlflow_airflow/docker/etl/" && docker build -t projectmlops_etl:latest .
        )
        build_docker_image_split = BashOperator(
            task_id="build_docker_split",
            bash_command=f"""
                export DOCKER_HOST=tcp://host.docker.internal:2375
                cd "/opt/airflow/docker/split_xy/" && docker build -t projectmlops_splitxy:latest .
                """,
        )
        build_docker_image_split = BashOperator(
            task_id="build_docker_train",
            bash_command=f"""
                export DOCKER_HOST=tcp://host.docker.internal:2375
                cd "/opt/airflow/docker/train/" && docker build -t projectmlops_train:latest .
                """,
        )

    etl_task = DockerOperator(
        task_id="etl",
        image="projectmlops_etl:latest",
        docker_url="tcp://host.docker.internal:2375",  # Pour Windows, et la comm entre container
        network_mode="bridge",
        auto_remove="force",
        command="python3 etl.py",
        mounts=[
            Mount(
                # source="/home/ubuntu/airflow/data/to_ingest",
                source=PROJECTMLOPS_PATH + "/data/raw_to_ingest",
                # source=os.getenv("APP_DATA_LOCALHOST_DIR") + "/to_ingest", # permet de ne pas mettre le chemin en dur
                target="/app/data/raw_to_ingest",
                type="bind",
            ),
            Mount(
                # source="/home/ubuntu/airflow/data/to_ingest",
                source=PROJECTMLOPS_PATH + "/data/raw_ingested",
                target="/app/data/raw_ingested",
                type="bind",
            ),
        ],
    )
    splitxy_task = DockerOperator(
        task_id="split_xy",
        image="projectmlops_splitxy:latest",
        docker_url="tcp://host.docker.internal:2375",  # Pour Windows, et la comm entre container
        network_mode="bridge",
        auto_remove="force",
        command="python3 split_xy.py",
        mounts=[
            Mount(
                # source="/home/ubuntu/airflow/data/to_ingest",
                source=PROJECTMLOPS_PATH + "/data/raw_ingested",
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

    train_task = DockerOperator(
        task_id="train",
        image="projectmlops_train:latest",
        docker_url="tcp://host.docker.internal:2375",  # Pour Windows, et la comm entre container
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

    # with TaskGroup("train_model") as group_train_model:
    #     my_task4 = PythonOperator(
    #         task_id="train_LinearRegression",
    #         python_callable=train_LinearRegression
    #     )
    #     my_task5 = PythonOperator(
    #         task_id="train_DecisionTreeRegressor",
    #         python_callable=train_DecisionTreeRegressor
    #     )

    # my_task6 = PythonOperator(
    #     task_id="train_best_model",
    #     python_callable=train_best_model
    # )

    fs_defaut_conn_task >> raw_sensor
    raw_sensor >> group_build_docker_image >> etl_task >> splitxy_task >> train_task
