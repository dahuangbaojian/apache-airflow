# syntax=docker/dockerfile:1.7

ARG AIRFLOW_VERSION=3.1.8
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ARG PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn
ARG APT_MIRROR_HOST=mirrors.tuna.tsinghua.edu.cn
FROM apache/airflow:${AIRFLOW_VERSION}

ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ARG PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn
ARG APT_MIRROR_HOST=mirrors.tuna.tsinghua.edu.cn

USER root

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV PIP_INDEX_URL=${PIP_INDEX_URL}
ENV PIP_TRUSTED_HOST=${PIP_TRUSTED_HOST}

# Switch Debian sources to a configurable mirror to speed up apt in CN networks.
RUN sed -i "s|http://deb.debian.org|https://${APT_MIRROR_HOST}|g; s|http://security.debian.org|https://${APT_MIRROR_HOST}|g" /etc/apt/sources.list.d/debian.sources

# Playwright browser runtime dependencies for Debian-based Airflow images.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcairo2 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    libxshmfence1 \
    openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /ms-playwright \
    && chown -R airflow:0 /ms-playwright \
    && chmod -R 755 /ms-playwright

USER airflow

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY --chown=airflow:0 wheels /tmp/wheels
RUN find /tmp/wheels -maxdepth 1 -type f -name "*.whl" \
    | sort \
    | while IFS= read -r wheel; do \
    pip install --no-cache-dir "$wheel"; \
    done

RUN python -c "import importlib.util; assert importlib.util.find_spec('playwright'), 'playwright is not installed. Add it to requirements.txt or wheel dependencies.'" \
    && playwright install chromium

USER root
RUN chmod -R 755 /ms-playwright

USER airflow

COPY --chown=airflow:0 dags /opt/airflow/dags
COPY --chown=airflow:0 plugins /opt/airflow/plugins
COPY --chown=airflow:0 config /opt/airflow/config
