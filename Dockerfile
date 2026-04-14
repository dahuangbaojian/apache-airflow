# syntax=docker/dockerfile:1.7

ARG AIRFLOW_VERSION=3.1.6
FROM apache/airflow:${AIRFLOW_VERSION}

USER root

# Keep system packages small. Add only the OS libraries your DAGs actually need.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

USER airflow

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY --chown=airflow:0 wheels /tmp/wheels
RUN find /tmp/wheels -maxdepth 1 -type f -name "*.whl" \
    | sort \
    | while IFS= read -r wheel; do \
    pip install --no-cache-dir "$wheel"; \
    done

COPY --chown=airflow:0 projects /opt/airflow/projects

# Optional source-package fallback. Prefer wheels for production releases.
RUN find /opt/airflow/projects -mindepth 1 -maxdepth 1 -type d \
    | while IFS= read -r project; do \
    if [ -f "$project/pyproject.toml" ] || [ -f "$project/setup.py" ]; then \
    pip install --no-cache-dir "$project"; \
    fi; \
    done

COPY --chown=airflow:0 dags /opt/airflow/dags
COPY --chown=airflow:0 plugins /opt/airflow/plugins
COPY --chown=airflow:0 config /opt/airflow/config
