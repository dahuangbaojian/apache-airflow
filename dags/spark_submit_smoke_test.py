import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator


SPARK_TEST_CONN_ID = "spark_default"
SPARK_TEST_APPLICATION = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "spark_jobs",
    "smoke_test.py",
)
SPARK_SMOKE_EXECUTOR_CORES = 1
SPARK_SMOKE_EXECUTOR_INSTANCES = 1
SPARK_SMOKE_CORES_MAX = "1"
SPARK_SMOKE_EXECUTOR_MEMORY = "1G"
SPARK_SMOKE_DRIVER_MEMORY = "1G"
SPARK_SMOKE_TIMEOUT_MINUTES = 5


with DAG(
    dag_id="spark_submit_smoke_test",
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    tags=["spark", "smoke"],
) as dag:
    SparkSubmitOperator(
        task_id="run_spark_smoke_test",
        conn_id=SPARK_TEST_CONN_ID,
        application=SPARK_TEST_APPLICATION,
        name="airflow-spark-smoke-test",
        executor_cores=SPARK_SMOKE_EXECUTOR_CORES,
        num_executors=SPARK_SMOKE_EXECUTOR_INSTANCES,
        executor_memory=SPARK_SMOKE_EXECUTOR_MEMORY,
        driver_memory=SPARK_SMOKE_DRIVER_MEMORY,
        status_poll_interval=5,
        retries=0,
        execution_timeout=timedelta(minutes=SPARK_SMOKE_TIMEOUT_MINUTES),
        conf={
            "spark.ui.showConsoleProgress": "false",
            "spark.cores.max": SPARK_SMOKE_CORES_MAX,
            "spark.executor.instances": SPARK_SMOKE_EXECUTOR_INSTANCES,
            "spark.executor.cores": SPARK_SMOKE_EXECUTOR_CORES,
            "spark.executor.memory": SPARK_SMOKE_EXECUTOR_MEMORY,
            "spark.driver.memory": SPARK_SMOKE_DRIVER_MEMORY,
            "spark.pyspark.python": "python3",
            "spark.pyspark.driver.python": "python3",
            "spark.task.maxFailures": "1",
            "spark.stage.maxConsecutiveAttempts": "1",
            "spark.deploy.maxExecutorRetries": "0",
        },
        verbose=False,
    )
