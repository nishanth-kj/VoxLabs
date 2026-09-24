# Headless REST API only (the product UI is the desktop app).
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg libsndfile1 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /voxlabs
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY app ./app

ENV VOXLABS_DATA_DIR=/data PYTHONUNBUFFERED=1
VOLUME /data
EXPOSE 8000
# Inside the container the API must listen on 0.0.0.0; set VOXLABS_API_TOKEN when publishing the port.
CMD ["uv", "run", "--no-sync", "uvicorn", "app.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
