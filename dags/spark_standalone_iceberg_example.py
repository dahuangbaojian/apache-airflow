from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import pyspark
from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _maybe_env(name: str) -> str | None:
    value = os.environ.get(name)
    return value if value else None


def _task_env() -> dict[str, str]:
    names = [
        "ICEBERG_CATALOG_NAME",
        "ICEBERG_CATALOG_TYPE",
        "ICEBERG_CATALOG_URI",
        "ICEBERG_WAREHOUSE",
        "ICEBERG_S3_ENDPOINT",
        "ICEBERG_S3_ACCESS_KEY_ID",
        "ICEBERG_S3_SECRET_ACCESS_KEY",
        "ICEBERG_S3_PATH_STYLE_ACCESS",
    ]
    return {name: value for name in names if (value := _maybe_env(name)) is not None}


def _iceberg_jars() -> str:
    jars_dir = Path(pyspark.__file__).resolve().parent / "jars"
    jar_names = [
        _env("ICEBERG_AWS_JAR", "iceberg-aws-bundle-1.10.1.jar"),
        _env("ICEBERG_SPARK_RUNTIME_JAR", "iceberg-spark-runtime-3.5_2.12-1.10.1.jar"),
    ]
    return ",".join(str(jars_dir / jar_name) for jar_name in jar_names)


with DAG(
    dag_id="spark_standalone_iceberg_example",
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    tags=["spark", "iceberg", "standalone"],
) as dag:
    SparkSubmitOperator(
        task_id="show_iceberg_namespaces",
        conn_id="spark_default",
        application="/opt/airflow/dags/jobs/iceberg_smoke.py",
        name="airflow-iceberg-namespace-check",
        jars=_iceberg_jars(),
        deploy_mode=_env("SPARK_DEPLOY_MODE", "client"),
        env_vars=_task_env(),
        application_args=[
            "--catalog",
            _env("ICEBERG_CATALOG_NAME", "iceberg_local"),
        ],
        conf={
            "spark.sql.extensions": "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
            "spark.driver.host": _required_env("SPARK_DRIVER_HOST"),
            "spark.driver.bindAddress": "0.0.0.0",
            "spark.driver.port": _env("SPARK_DRIVER_PORT", "45689"),
            "spark.blockManager.port": _env("SPARK_BLOCKMANAGER_PORT", "45690"),
        },
    )
