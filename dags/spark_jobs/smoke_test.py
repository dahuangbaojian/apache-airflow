import argparse

from pyspark.sql import SparkSession


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--partitions", type=int, default=2)
    parser.add_argument("--count", type=int, default=1000)
    return parser.parse_args()


def main():
    args = parse_args()

    spark = (
        SparkSession.builder.appName("airflow-spark-smoke-test")
        .config("spark.sql.shuffle.partitions", str(args.partitions))
        .getOrCreate()
    )

    try:
        total = spark.range(0, args.count, 1, args.partitions).count()
        print(f"spark_version={spark.version}")
        print(f"partitions={args.partitions}")
        print(f"count={total}")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
