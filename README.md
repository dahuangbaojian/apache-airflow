# Airflow Docker Compose Ops

Airflow 3 with CeleryExecutor, Postgres, Redis, and a custom image.

## Model

- Build in test/CI
- Push image to Harbor
- Production only `pull` and `up -d`
- Business code enters the image through `wheels/`
- DAG files under `dags/` are copied into the image

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

## Build and Push

```bash
docker compose -f docker-compose.yml -f docker-compose.build.yml build airflow-api-server
docker tag local/airflow:3.1.8 harbor.example.com/team/airflow:3.1.8-YYYYMMDD
docker login harbor.example.com
docker push harbor.example.com/team/airflow:3.1.8-YYYYMMDD
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
- `playwright install chromium`: browser download is usually the remaining bottleneck
