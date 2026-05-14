# syntax=docker/dockerfile:1.7

ARG AIRFLOW_VERSION=3.1.8
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ARG PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn
ARG APT_MIRROR_HOST=mirrors.tuna.tsinghua.edu.cn
ARG ICEBERG_VERSION=1.10.1
ARG ICEBERG_SPARK_RUNTIME_ARTIFACT=iceberg-spark-runtime-3.5_2.12
ARG ICEBERG_AWS_ARTIFACT=iceberg-aws-bundle
FROM apache/airflow:${AIRFLOW_VERSION}-python3.13

ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ARG PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn
ARG APT_MIRROR_HOST=mirrors.tuna.tsinghua.edu.cn
ARG ICEBERG_VERSION=1.10.1
ARG ICEBERG_SPARK_RUNTIME_ARTIFACT=iceberg-spark-runtime-3.5_2.12
ARG ICEBERG_AWS_ARTIFACT=iceberg-aws-bundle

USER root

ENV PIP_INDEX_URL=${PIP_INDEX_URL}
ENV PIP_TRUSTED_HOST=${PIP_TRUSTED_HOST}

# Switch Debian sources to a configurable mirror to speed up apt in CN networks.
RUN sed -i "s|http://deb.debian.org|https://${APT_MIRROR_HOST}|g; s|http://security.debian.org|https://${APT_MIRROR_HOST}|g" /etc/apt/sources.list.d/debian.sources

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*

USER airflow

COPY requirements.txt /tmp/requirements.txt
COPY --chown=airflow:0 wheels /tmp/wheels
RUN pip install --no-cache-dir --find-links /tmp/wheels -r /tmp/requirements.txt

COPY --chown=airflow:0 jars /tmp/jars
RUN JARS_DIR="$(python -c "import pathlib, pyspark; print(pathlib.Path(pyspark.__file__).resolve().parent / 'jars')")" \
    && AWS_JAR="${ICEBERG_AWS_ARTIFACT}-${ICEBERG_VERSION}.jar" \
    && SPARK_RUNTIME_JAR="${ICEBERG_SPARK_RUNTIME_ARTIFACT}-${ICEBERG_VERSION}.jar" \
    && test -f "/tmp/jars/${AWS_JAR}" \
    && test -f "/tmp/jars/${SPARK_RUNTIME_JAR}" \
    && cp "/tmp/jars/${AWS_JAR}" "${JARS_DIR}/${AWS_JAR}" \
    && cp "/tmp/jars/${SPARK_RUNTIME_JAR}" "${JARS_DIR}/${SPARK_RUNTIME_JAR}"

RUN find /tmp/wheels -maxdepth 1 -type f -name "*.whl" \
    | sort \
    | while IFS= read -r wheel; do \
    pip install --no-cache-dir --find-links /tmp/wheels "$wheel"; \
    done

COPY --chown=airflow:0 spark-pyfiles /opt/airflow/spark-pyfiles
COPY --chown=airflow:0 models /opt/airflow/models

ENV EMBEDDING_MODELS_DIR=/opt/airflow/models/embedding \
    HF_HOME=/opt/airflow/.cache/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/opt/airflow/models \
    TRANSFORMERS_OFFLINE=1 \
    HF_HUB_OFFLINE=1

RUN mkdir -p "${HF_HOME}"

COPY --chown=airflow:0 dags /opt/airflow/dags
COPY --chown=airflow:0 plugins /opt/airflow/plugins
COPY --chown=airflow:0 config /opt/airflow/config
