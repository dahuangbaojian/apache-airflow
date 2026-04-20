from datetime import datetime

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator


def print_runtime_info():
    import os
    import platform
    import sys

    print("python_smoke_test=ok")
    print(f"python_version={sys.version}")
    print(f"platform={platform.platform()}")
    print(f"hostname={platform.node()}")
    print(f"cwd={os.getcwd()}")


with DAG(
    dag_id="python_smoke_test",
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    tags=["python", "smoke"],
) as dag:
    PythonOperator(
        task_id="print_runtime_info",
        python_callable=print_runtime_info,
    )
