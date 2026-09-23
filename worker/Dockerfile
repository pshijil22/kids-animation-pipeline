FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    espeak-ng \
    ffmpeg \
    git \
    build-essential \
    libsndfile1 \
    libsndfile1-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
# Use torch CPU version to reduce image size (use GPU image variant for CUDA)
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p /data/stories /data/audio /data/scenes /data/videos /data/logs /data/music

# Set environment variables
ENV DATA_DIR=/data
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run worker
CMD ["python", "app.py"]
