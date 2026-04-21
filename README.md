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
SPARK_MASTER_URL=spark://host.docker.internal:7077
SPARK_DEPLOY_MODE=client
```

Apollo example:

```env
APOLLO_APP_ID=datacenter-task
APOLLO_CONFIG_SERVICE_URL=http://apollo.example.com:8080
APOLLO_CLUSTER=default
APOLLO_NAMESPACES=application
```

`APOLLO_CONFIG_SERVICE_URL` only needs the service root.

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

This supports submitting jobs from Airflow to an existing Spark cluster.

Put these files into the repo's [jars/README.md](/Users/huangjian/docker/apache-airflow/jars/README.md) directory before building:

- `iceberg-aws-bundle-1.10.1.jar`
- `iceberg-spark-runtime-3.5_2.12-1.10.1.jar`

The Docker build copies them into the `pyspark` `jars/` directory inside the image.

Before using Spark DAGs:

1. Make sure `pyspark` matches the Spark cluster minor version
2. Set `SPARK_MASTER_URL` in `.env` to the host Spark master address such as `spark://host.docker.internal:7077`
3. Keep the default `SPARK_DEPLOY_MODE=client` unless your cluster nodes cannot reach the Airflow worker container
4. Create an Airflow Spark connection such as `spark_default`
5. If you upgrade Spark or Iceberg, update `ICEBERG_VERSION` or `ICEBERG_SPARK_RUNTIME_ARTIFACT` in `Dockerfile`, then put the matching jar files into `jars/`

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

Minimal DAG example:

```python
import os
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
        application="/opt/airflow/dags/jobs/example.py",
        deploy_mode=os.environ.get("SPARK_DEPLOY_MODE", "client"),
        conf={
            "spark.master": os.environ["SPARK_MASTER_URL"],
        },
    )
```

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
