# VoxLabs Backend Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml .

# Install dependencies with uv
RUN uv pip install --system -r pyproject.toml

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p voice_projects/voices static/audio

# Expose port
EXPOSE 8000

# Set Python path
ENV PYTHONPATH=/app

# Run FastAPI backend with uv
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
