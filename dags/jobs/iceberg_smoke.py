from __future__ import annotations

import argparse
import os

from pyspark.sql import SparkSession


def _env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if value is None or value == "":
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _bool_text(name: str, default: str = "false") -> str:
    return str(_env(name, default)).strip().lower()


def build_spark_session(app_name: str, catalog_name: str) -> SparkSession:
    catalog_type = _env("ICEBERG_CATALOG_TYPE", "hadoop")
    warehouse = _env("ICEBERG_WAREHOUSE")
    s3_endpoint = _env("ICEBERG_S3_ENDPOINT")
    s3_access_key = _env("ICEBERG_S3_ACCESS_KEY_ID")
    s3_secret_key = _env("ICEBERG_S3_SECRET_ACCESS_KEY")
    s3_path_style = _bool_text("ICEBERG_S3_PATH_STYLE_ACCESS", "true")

    builder = SparkSession.builder.appName(app_name)
    config = {
        "spark.sql.extensions": "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
        f"spark.sql.catalog.{catalog_name}": "org.apache.iceberg.spark.SparkCatalog",
        f"spark.sql.catalog.{catalog_name}.type": catalog_type,
        f"spark.sql.catalog.{catalog_name}.warehouse": warehouse,
        f"spark.sql.catalog.{catalog_name}.io-impl": "org.apache.iceberg.aws.s3.S3FileIO",
        f"spark.sql.catalog.{catalog_name}.s3.endpoint": s3_endpoint,
        f"spark.sql.catalog.{catalog_name}.s3.access-key-id": s3_access_key,
        f"spark.sql.catalog.{catalog_name}.s3.secret-access-key": s3_secret_key,
        f"spark.sql.catalog.{catalog_name}.s3.path-style-access": s3_path_style,
    }
    for key, value in config.items():
        builder = builder.config(key, value)
    return builder.getOrCreate()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write a small dataset into an Iceberg table and read it back.")
    parser.add_argument("--catalog", default=_env("ICEBERG_CATALOG_NAME", "iceberg_local"))
    parser.add_argument("--namespace", default=_env("ICEBERG_NAMESPACE", "demo"))
    parser.add_argument("--table", default=_env("ICEBERG_TABLE", "events"))
    parser.add_argument("--app-name", default="airflow-iceberg-smoke")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    spark = build_spark_session(args.app_name, args.catalog)
    full_namespace = f"{args.catalog}.{args.namespace}"
    full_table_name = f"{full_namespace}.{args.table}"

    spark.sql(f"CREATE NAMESPACE IF NOT EXISTS {full_namespace}")

    rows = [
        (1, "signup", "2026-01-01T00:00:00"),
        (2, "purchase", "2026-01-01T00:05:00"),
        (3, "refund", "2026-01-01T00:10:00"),
    ]
    df = spark.createDataFrame(rows, ["event_id", "event_type", "event_ts"])

    (
        df.writeTo(full_table_name)
        .using("iceberg")
        .tableProperty("format-version", "2")
        .createOrReplace()
    )

    result = spark.read.table(full_table_name).orderBy("event_id")
    result.show(truncate=False)
    print(f"Wrote {result.count()} rows to {full_table_name}")
    spark.stop()


if __name__ == "__main__":
    main()
