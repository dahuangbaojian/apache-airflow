from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from datetime import datetime

def print_hello():
    print("Hello Airflow!")

def print_world():
    print("World")

with DAG(
    dag_id="demo_python_hello",
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
) as dag:
    t1 = PythonOperator(
        task_id="print_hello",
        python_callable=print_hello,
    )
    t2 = PythonOperator(
        task_id="print_world",
        python_callable=print_world,
    )
    t1 >> t2