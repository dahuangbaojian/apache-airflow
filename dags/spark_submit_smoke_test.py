import os
from datetime import datetime

from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator


SPARK_TEST_CONN_ID = os.getenv("SPARK_TEST_CONN_ID", "spark_default")
SPARK_TEST_APPLICATION = os.getenv(
    "SPARK_TEST_APPLICATION",
    "/opt/airflow/dags/spark_jobs/smoke_test.py",
)


with DAG(
    dag_id="spark_submit_smoke_test",
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    tags=["spark", "smoke"],
) as dag:
    SparkSubmitOperator(
        task_id="run_spark_smoke_test",
        conn_id=SPARK_TEST_CONN_ID,
        application=SPARK_TEST_APPLICATION,
        name="airflow-spark-smoke-test",
        application_args=["--partitions", "2", "--count", "1000"],
        conf={
            "spark.ui.showConsoleProgress": "false",
        },
        verbose=False,
    )
