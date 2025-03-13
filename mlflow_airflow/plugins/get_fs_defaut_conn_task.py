from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow import settings
from airflow.models.connection import Connection

fs_default_conn_conf = {
    "conn_id": "fs_default",
    "conn_type": "File",
    "host": "/opt/airflow/",
    # "host": "/app/",
    "login": None,
    "password": None,
    "schema": None,
}

conn_keys = ["conn_id", "conn_type", "host", "login", "password", "schema"]


def create_conn(**kwargs):
    session = settings.Session()
    print("Session created")
    connections = session.query(Connection)
    print("Connections listed")
    if not kwargs["conn_id"] in [connection.conn_id for connection in connections]:
        conn_params = {key: kwargs[key] for key in conn_keys}
        conn = Connection(**conn_params)
        session.add(conn)
        session.commit()
        print("Connection Created")
    else:
        print("Connection already exists")
    session.close()


def get_fs_defaut_conn_task(dag: DAG):
    create_fs_default_conn = PythonOperator(
        task_id="create_fs_default_conn",
        python_callable=create_conn,
        op_kwargs=fs_default_conn_conf,
        dag=dag,
    )
    return create_fs_default_conn
