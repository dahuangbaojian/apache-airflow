# Airflow Docker Compose Ops

Airflow 3 with CeleryExecutor, Postgres, Redis, and a custom image.

## Model

- Build in test/CI
- Push image to Harbor
- Production only `pull` and `up -d`
- Business code enters the image through `wheels/`
- DAG files under `dags/` are copied into the image
- Spark task submission is supported through Airflow's Spark provider

## Files

- `docker-compose.yml`: runtime
- `docker-compose.build.yml`: build only
- `Dockerfile`: custom image
- `.env.example`: env template
- `admin-password.sh`: print admin password

## Required Runtime Env

```env
AIRFLOW_IMAGE_NAME=harbor.example.com/team/airflow:3.1.8-YYYYMMDD
AIRFLOW_UID=50000

AIRFLOW_POSTGRES_USER=airflow
AIRFLOW_POSTGRES_PASSWORD=replace-me
AIRFLOW_POSTGRES_DB=airflow
AIRFLOW_REDIS_PASSWORD=replace-me

FERNET_KEY=replace-me
SECRET_KEY=replace-me
JWT_SECRET=replace-me

AIRFLOW_API_PORT=18081
AIRFLOW_TIMEZONE=Asia/Shanghai
TZ=Asia/Shanghai
AIRFLOW_LOGGING_LEVEL=INFO
AIRFLOW_WORKER_LOG_SERVER_PORT=8793
SPARK_MASTER_URL=spark://host.docker.internal:7077
SPARK_DEPLOY_MODE=client
ICEBERG_CATALOG_NAME=iceberg_local
ICEBERG_CATALOG_TYPE=hadoop
ICEBERG_WAREHOUSE=s3://warehouse/iceberg
ICEBERG_S3_ENDPOINT=http://minio.example.com:9000
ICEBERG_S3_ACCESS_KEY_ID=replace-me
ICEBERG_S3_SECRET_ACCESS_KEY=replace-me
ICEBERG_S3_PATH_STYLE_ACCESS=true
```

Apollo example:

```env
APOLLO_APP_ID=datacenter-task
APOLLO_CONFIG_SERVICE_URL=http://apollo.example.com:8080
APOLLO_CLUSTER=default
APOLLO_NAMESPACES=application
```

`APOLLO_CONFIG_SERVICE_URL` only needs the service root.

For Celery task log streaming, `docker-compose.yml` also sets:

- `AIRFLOW__LOGGING__WORKER_LOG_SERVER_PORT=${AIRFLOW_WORKER_LOG_SERVER_PORT:-8793}`
- `AIRFLOW__CORE__HOSTNAME_CALLABLE=airflow.utils.net.get_host_ip_address`

This avoids broken worker log URLs such as `http://:8793/...` when Airflow cannot derive a usable container hostname.

## Build Env

Used only when building:

```env
AIRFLOW_VERSION=3.1.8
APT_MIRROR_HOST=mirrors.tuna.tsinghua.edu.cn
PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn
```

## Spark Support

The image includes:

- `apache-airflow-providers-apache-spark`
- `pyspark`
- Java runtime
- Iceberg runtime jars for Spark and AWS access

This supports submitting jobs from Airflow workers to a Spark standalone cluster running on the Docker host.

Put these files into the repo's [jars/README.md](/Users/huangjian/docker/apache-airflow/jars/README.md) directory before building:

- `iceberg-aws-bundle-1.10.1.jar`
- `iceberg-spark-runtime-3.5_2.12-1.10.1.jar`

The Docker build copies them into the `pyspark` `jars/` directory inside the image.

Before using Spark DAGs:

1. Make sure `pyspark` matches the Spark cluster minor version
2. Set `SPARK_MASTER_URL` in `.env` to the host Spark master address such as `spark://host.docker.internal:7077`
3. Keep the default `SPARK_DEPLOY_MODE=client` unless your cluster nodes cannot reach the Airflow worker container
4. Set `ICEBERG_WAREHOUSE` to an `s3://...` warehouse path and configure the matching S3-compatible endpoint and credentials
5. If you upgrade Spark or Iceberg, update `ICEBERG_VERSION` or `ICEBERG_SPARK_RUNTIME_ARTIFACT` in `Dockerfile`, then put the matching jar files into `jars/`

`AIRFLOW_CONN_SPARK_DEFAULT` is still present inside `docker-compose.yml` because Airflow's Spark provider reads connection settings from that environment variable. You do not need to set it in `.env` unless you intentionally want it to differ from `SPARK_MASTER_URL`.

`docker-compose.yml` already injects a Linux-compatible host alias:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

This lets Airflow containers reach services that are running directly on the Docker host.

Host Spark prerequisites:

- Spark master must listen on a non-loopback address, not only `127.0.0.1`
- Spark master should advertise a host/IP that Airflow containers can reach
- `7077` must be reachable from the Docker bridge network
- Spark workers must be able to reach your Iceberg object storage endpoint; do not use a hostname that only the Airflow containers can resolve

Iceberg storage prerequisites:

- Use an `s3://bucket/prefix` warehouse path when using Iceberg `S3FileIO`
- `ICEBERG_S3_ENDPOINT` must be reachable from the Spark workers, not only from the Airflow containers
- For MinIO or other S3-compatible stores, set `ICEBERG_S3_PATH_STYLE_ACCESS=true`
- In production, move `ICEBERG_S3_ACCESS_KEY_ID` and `ICEBERG_S3_SECRET_ACCESS_KEY` to a real secret backend rather than leaving them in plain environment variables

Validate connectivity from a worker:

```bash
docker compose exec airflow-worker getent hosts host.docker.internal
docker compose exec airflow-worker python - <<'PY'
import socket

host = "host.docker.internal"
port = 7077
with socket.create_connection((host, port), timeout=3):
    print(f"connected to {host}:{port}")
PY
```

If you use standalone Spark and executors cannot connect back to a driver running inside the Airflow worker container, switch to `SPARK_DEPLOY_MODE=cluster` and place the application file on storage that the Spark cluster can read.

Included example files:

- [dags/spark_standalone_iceberg_example.py](/Users/huangjian/docker/apache-airflow/dags/spark_standalone_iceberg_example.py): Airflow DAG that calls `spark-submit`
- [dags/jobs/iceberg_smoke.py](/Users/huangjian/docker/apache-airflow/dags/jobs/iceberg_smoke.py): PySpark app that runs `SHOW NAMESPACES IN <catalog>`

The DAG submits the two Iceberg jars that are baked into the Airflow image to the standalone cluster using the operator's `jars=` parameter. That means the host Spark workers do not need those jars preinstalled in `SPARK_HOME/jars`.

Example DAG:

```python
from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime

with DAG(
    dag_id="spark_submit_example",
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
) as dag:
    SparkSubmitOperator(
        task_id="run_spark_job",
        conn_id="spark_default",
        application="/opt/airflow/dags/jobs/iceberg_smoke.py",
        deploy_mode="client",
        jars="/path/to/iceberg-aws-bundle.jar,/path/to/iceberg-spark-runtime.jar",
    )
```

The sample job configures Iceberg like this inside `SparkSession.builder`:

```text
spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions
spark.sql.catalog.iceberg_local=org.apache.iceberg.spark.SparkCatalog
spark.sql.catalog.iceberg_local.type=hadoop
spark.sql.catalog.iceberg_local.warehouse=s3://warehouse/iceberg
spark.sql.catalog.iceberg_local.io-impl=org.apache.iceberg.aws.s3.S3FileIO
spark.sql.catalog.iceberg_local.s3.endpoint=http://minio.example.com:9000
spark.sql.catalog.iceberg_local.s3.access-key-id=replace-me
spark.sql.catalog.iceberg_local.s3.secret-access-key=replace-me
spark.sql.catalog.iceberg_local.s3.path-style-access=true
```

Then it runs:

```sql
SHOW NAMESPACES IN iceberg_local
```

Rollout steps:

1. Update `.env` with the real `SPARK_MASTER_URL` and Iceberg storage settings
2. Build a new Airflow image because the DAG files are copied into the image at build time:

```bash
docker compose -f docker-compose.yml -f docker-compose.build.yml build airflow-api-server
```

3. Recreate the Airflow services:

```bash
docker compose up -d --force-recreate airflow-api-server airflow-scheduler airflow-worker airflow-triggerer airflow-dag-processor
```

4. Confirm the worker can reach the host Spark master:

```bash
docker compose exec airflow-worker getent hosts host.docker.internal
docker compose exec airflow-worker python - <<'PY'
import socket

with socket.create_connection(("host.docker.internal", 7077), timeout=3):
    print("spark master reachable")
PY
```

5. Trigger `spark_standalone_iceberg_example` from Airflow UI
6. Check the task log for the `SHOW NAMESPACES` output and the final `Listed namespaces from Iceberg catalog ...` line

## Build and Push

```bash
docker compose -f docker-compose.yml -f docker-compose.build.yml build airflow-api-server
docker tag local/airflow:3.1.8 harbor.example.com/team/airflow:3.1.8-YYYYMMDD
docker login harbor.example.com
docker push harbor.example.com/team/airflow:3.1.8-YYYYMMDD
```

To verify the built image contains the Iceberg jars:

```bash
docker run --rm local/airflow:3.1.8 bash -lc 'python - <<'"'"'PY'"'"'
import pathlib
import pyspark

jars_dir = pathlib.Path(pyspark.__file__).resolve().parent / "jars"
for path in sorted(jars_dir.glob("*iceberg*.jar")):
    print(path.name)
PY'
```

Use immutable tags such as date, build number, or commit SHA.

## First Deployment

```bash
docker compose pull
docker compose up airflow-init
docker compose up -d
```

## Normal Release

1. Update `AIRFLOW_IMAGE_NAME` in `.env`
2. Run:

```bash
docker compose pull
docker compose up -d
```

If the image includes Airflow schema changes:

```bash
docker compose up airflow-init
```

## Rollback

1. Set `AIRFLOW_IMAGE_NAME` back to the previous tag
2. Run:

```bash
docker compose pull
docker compose up -d
```

## Safer Release

If tasks are running, update more carefully:

```bash
docker compose stop airflow-scheduler
# wait for running tasks to finish
docker compose pull
docker compose up -d
docker compose start airflow-scheduler
```

## Access

Airflow UI:

```text
http://localhost:18081
```

Admin password:

```bash
bash admin-password.sh
```

## Common Commands

```bash
docker compose ps
docker compose logs --tail=200 airflow-api-server
docker compose logs --tail=200 airflow-scheduler
docker compose logs --tail=200 airflow-worker
docker compose logs --tail=200 airflow-dag-processor
```

## Troubleshooting

Database URL parse errors such as `123!@airflow-postgres`:

- Postgres password likely contains URI-special characters
- Avoid `@ : / ? # %`

Harbor push fails with `no basic auth credentials`:

```bash
docker login harbor.example.com
```

Harbor pull fails:

```bash
getent hosts harbor.example.com
curl -vk https://harbor.example.com/v2/
nc -vz harbor.example.com 443
nc -vz harbor.example.com 80
```

Build is slow:

- `apt-get`: check `APT_MIRROR_HOST`
- `pip install`: check `PIP_INDEX_URL`
- This image no longer installs `playwright` or browser binaries during build.
