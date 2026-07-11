# syntax=docker/dockerfile:1.7
# Multi-stage Dockerfile for the FastAPI backend.
#
# Stage 1 (builder) installs Python deps into a venv. Stage 2 copies the
# venv plus the source. Final image runs as a non-root user, exposes
# port 8000, and starts uvicorn.
#
# Build:    docker build -f backend/Dockerfile -t pms-backend ./backend
# Run:      docker run -p 8000:8000 --env-file backend/.env pms-backend
# Tag tip:  pin to your CI commit sha for reproducibility.

# ---- Stage 1: builder ------------------------------------------------------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# WeasyPrint needs cairo + pango etc. They're large; install only when
# the OPTIONAL_DEPS arg is set to keep slim builds slim.
ARG OPTIONAL_DEPS=false
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
    && if [ "$OPTIONAL_DEPS" = "true" ]; then \
        apt-get install -y --no-install-recommends \
            libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
            libgdk-pixbuf-2.0-0 shared-mime-info ; \
       fi \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Cache pip downloads on the BuildKit cache mount.
COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt

# ---- Stage 2: runtime ------------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_ENV=production

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app && useradd --system --gid app --no-create-home app

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

# Copy source last so dep changes don't bust the source layer cache.
COPY --chown=app:app . /app

USER app

EXPOSE 8000

# Healthcheck hits /live (k8s-style: alive iff process is up — no DB hit).
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl --fail --silent http://127.0.0.1:8000/live || exit 1

# Default to two uvicorn workers; overridable via env. Use the structured
# logging configured in app.core.logging_config (already runs at import time).
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-2} --proxy-headers --forwarded-allow-ips=*"]
