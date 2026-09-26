# VoxLabs REST API + MCP server, headless. The product UI is the desktop app, so this image has no Qt.
#
#   docker build -t voxlabs-api .                          # engines: --build-arg EXTRAS="piper kokoro"
#   docker run --rm -p 127.0.0.1:8942:8942 -e VOXLABS_API_TOKEN=change-me -v voxlabs_data:/data voxlabs-api
#
# The server listens on 0.0.0.0 inside the container, so it refuses to start without VOXLABS_API_TOKEN.
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg libsndfile1 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
WORKDIR /voxlabs

# Optional engine extras from pyproject.toml, space separated (xtts, f5 and chatterbox exclude each other).
ARG EXTRAS=""
COPY pyproject.toml uv.lock ./
# PySide6 is only needed by the desktop UI; the API never imports Qt.
RUN uv sync --frozen --no-dev --no-install-project \
        --no-install-package pyside6 --no-install-package pyside6-essentials \
        --no-install-package pyside6-addons --no-install-package shiboken6 \
        $(for extra in $EXTRAS; do printf -- '--extra %s ' "$extra"; done)
COPY app ./app

RUN useradd --create-home --uid 1000 voxlabs \
    && mkdir /data \
    && chown voxlabs /data
USER voxlabs

ENV VOXLABS_DATA_DIR=/data \
    PYTHONUNBUFFERED=1 \
    PATH="/voxlabs/.venv/bin:$PATH"
VOLUME /data
EXPOSE 8942
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8942/api/health', timeout=4)"]
CMD ["python", "-m", "app.api.app", "--host", "0.0.0.0", "--port", "8942"]
