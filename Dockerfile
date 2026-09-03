# ReelPilot — single-process bot + dashboard, engineered for 256MB RAM.
# Multi-stage keeps the runtime image lean (<300MB); no browsers ever.

# ---- Stage 1: wheels -------------------------------------------------------
FROM python:3.11-slim AS builder
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /build
COPY requirements.txt .
RUN pip wheel --wheel-dir /wheels -r requirements.txt

# ---- Stage 2: runtime -------------------------------------------------------
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 \
    MALLOC_ARENA_MAX=2 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1

# ffmpeg for frame extraction only — no GUI/browser libraries, no recommends.
RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-index --find-links=/wheels -r requirements.txt \
 && rm -rf /wheels

COPY config.py database.py ig_handler.py dashboard.py main.py ./
COPY static ./static

# Non-root runtime user. The Fly volume mounts at /data with root ownership,
# so the entrypoint chowns it once and then drops privileges via setpriv.
RUN useradd -m -u 10001 reelpilot \
 && mkdir -p /data/downloads \
 && chown -R reelpilot:reelpilot /data /app

# Health check hits the Flask /health endpoint on the internal port.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8080/health', timeout=4)" || exit 1

EXPOSE 8080
# One process: Telegram polling loop + dashboard thread, low-buffer startup.
ENTRYPOINT ["sh", "-c", "chown -R 10001:10001 /data 2>/dev/null || true; exec setpriv --reuid=10001 --regid=10001 --init-groups python -u main.py"]
