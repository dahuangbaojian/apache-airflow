# Airflow Docker Compose Deployment

This Compose project runs Airflow 3 with CeleryExecutor, Postgres, Redis, and a custom Airflow image.

## Deployment Model

Production uses one immutable Airflow image for every Airflow component:

- Python dependencies are installed from `requirements.txt` at image build time.
- Wheels under `wheels/` are installed at image build time.
- `dags/`, `plugins/`, and `config/` are copied into the image.
- Runtime state uses Docker named volumes.
- Local bind mounts are only used by `docker-compose.dev.yml`.
- Secrets stay in `.env` or a production secret manager, not in the image.
- `docker-compose.yml` is runtime-only; `docker-compose.build.yml` is used only when building the image locally.
- Playwright system dependencies and Chromium are installed by the image; browsers live under `/ms-playwright` with shared read/execute permissions, and the Python `playwright` package must come from `requirements.txt` or your wheel dependencies.

## First-Time Setup

Create the environment file:

```bash
cp .env.example .env
```

Edit `.env` and set strong values for:

- `AIRFLOW_POSTGRES_PASSWORD`
- `AIRFLOW_REDIS_PASSWORD`
- `FERNET_KEY`
- `SECRET_KEY`
- `JWT_SECRET`

Optional build acceleration:

- `PIP_INDEX_URL`
- `PIP_TRUSTED_HOST`

Generate a Fernet key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Production Run

Prefer wheel artifacts for Python project releases:

```text
wheels/
  my_python_project-1.0.0-py3-none-any.whl
```

Build the wheel in the Python project repository:

```bash
python -m build
```

Copy the generated `.whl` file into `wheels/`, then rebuild the Airflow image:

```bash
cp /path/to/my_python_project/dist/*.whl wheels/
docker compose -f docker-compose.yml -f docker-compose.build.yml build
docker compose up -d
```

Keep DAG files thin and import the package:

```python
from airflow.sdk import dag, task
from my_python_project.job import run_job

@dag(schedule=None, catchup=False)
def my_job():
    @task
    def run():
        run_job()

    run()

dag = my_job()
```

First-time build and start:

```bash
docker compose -f docker-compose.yml -f docker-compose.build.yml build
docker compose up airflow-init
docker compose up -d
```

Open Airflow at:

```text
http://localhost:18081
```

Read the generated Simple Auth Manager password:

```bash
./admin-password.sh
```

## Development Run

Use the dev override when you want Airflow to hot-load local edits:

```bash
docker compose -f docker-compose.yml -f docker-compose.build.yml build
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

The dev override bind-mounts:

- `./dags` to `/opt/airflow/dags`
- `./plugins` to `/opt/airflow/plugins`
- `./config` to `/opt/airflow/config`
- `./logs` to `/opt/airflow/logs`

When you change wheel artifacts or `requirements.txt`, rebuild the image:

```bash
docker compose -f docker-compose.yml -f docker-compose.build.yml build
docker compose up -d
```

## Notes

- Do not commit `.env`.
- Postgres and Redis are not exposed to the host by default.
- Put DAG-specific Python packages in `requirements.txt`.
- Keep `playwright` in `requirements.txt` or your wheel dependencies when DAG code uses browser automation.
- Use `docker compose --profile flower up -d flower` only when you need Flower.
