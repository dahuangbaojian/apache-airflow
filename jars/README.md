Put the Spark Iceberg jars used by the Airflow image in this directory.

Required files:

- `iceberg-aws-bundle-1.10.1.jar`
- `iceberg-spark-runtime-3.5_2.12-1.10.1.jar`

Download them from Maven Central:

```bash
curl -fL https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-aws-bundle/1.10.1/iceberg-aws-bundle-1.10.1.jar \
  -o jars/iceberg-aws-bundle-1.10.1.jar
curl -fL https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/1.10.1/iceberg-spark-runtime-3.5_2.12-1.10.1.jar \
  -o jars/iceberg-spark-runtime-3.5_2.12-1.10.1.jar
```

The Docker build copies these files into PySpark's `jars/` directory inside the image.

The default Dockerfile expects:

- `ICEBERG_VERSION=1.10.1`
- `ICEBERG_AWS_ARTIFACT=iceberg-aws-bundle`
- `ICEBERG_SPARK_RUNTIME_ARTIFACT=iceberg-spark-runtime-3.5_2.12`

If you upgrade Spark or Iceberg, update those Dockerfile `ARG` values and place the matching jar files in this directory.
