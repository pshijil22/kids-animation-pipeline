#!/bin/bash
# Quick start script for Kids Animation Pipeline

set -e

echo "==== Kids Animation Pipeline - Phase 1 Quick Start ===="
echo ""

# Step 1: Check Docker
echo "[1] Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed. Please install Docker Desktop."
    exit 1
fi
echo "✓ Docker found"
echo ""

# Step 2: Create .env if missing
echo "[2] Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env from .env.example"
else
    echo "✓ .env already exists"
fi
echo ""

# Step 3: Create data directories
echo "[3] Creating data directories..."
mkdir -p data/stories data/audio data/scenes data/videos data/logs
echo "✓ Data directories ready"
echo ""

# Step 4: Start services
echo "[4] Starting Docker services..."
docker compose up -d
echo "✓ Services started"
echo ""

# Step 5: Wait for services
echo "[5] Waiting for services to be ready (30 seconds)..."
sleep 30
echo "✓ Services should be ready"
echo ""

# Step 6: Pull Ollama model
echo "[6] Pulling Ollama model (this takes 5-10 minutes)..."
docker exec kids-channel-ollama ollama pull llama3.2:3b
echo "✓ Model ready"
echo ""

# Step 7: Verify Ollama
echo "[7] Verifying Ollama..."
docker exec kids-channel-ollama ollama list
echo ""

# Step 8: Test worker
echo "[8] Testing worker endpoint..."
curl -X POST http://localhost:8000/create 2>/dev/null | head -c 200
echo ""
echo ""
echo "==== SETUP COMPLETE ===="
echo ""
echo "Next steps:"
echo "1. Monitor logs: docker compose logs -f worker"
echo "2. Generate a story: curl -X POST http://localhost:8000/create"
echo "3. Check results: ls -la data/stories/"
echo "4. Open n8n UI: http://localhost:5678"
echo ""
