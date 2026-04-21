from pyspark.sql import SparkSession

def main():
    spark = SparkSession.builder.appName("airflow-spark-smoke-test").getOrCreate()

    try:
        total = spark.range(1).count()
        print(f"spark_version={spark.version}")
        print(f"count={total}")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
