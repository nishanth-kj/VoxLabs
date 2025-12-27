# VoxLabs Backend Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    libsndfile1-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from root
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy engine code
COPY engine/ ./engine/

# Create necessary directories
RUN mkdir -p voice_projects/voices static/audio

# Expose port
EXPOSE 8000

# Set Python path
ENV PYTHONPATH=/app

# Run FastAPI backend
CMD ["python", "backend/main.py"]
