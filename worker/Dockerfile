FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    espeak-ng \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m pip install --upgrade pip

# Copy application
COPY . .

# Create all data directories
RUN mkdir -p /data/stories /data/audio /data/scenes /data/videos /data/music /data/logs

# Environment variables
ENV DATA_DIR=/data
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run worker
CMD ["python", "app.py"]
