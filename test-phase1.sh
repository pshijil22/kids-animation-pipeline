#!/bin/bash
# Test script for Phase 1: Story Generation

echo "==== Testing Kids Animation Pipeline - Phase 1 ===="
echo ""

# Check if services are running
echo "[1] Checking services..."
docker compose ps
echo ""

# Check Ollama
echo "[2] Testing Ollama connection..."
docker exec kids-channel-ollama ollama list
echo ""

# Check worker health
echo "[3] Testing worker health..."
curl -s http://localhost:8000/health | python -m json.tool
echo ""

# Generate a story
echo "[4] Generating a test story..."
echo "(This may take 1-2 minutes on CPU-only systems)"
echo ""

RESPONSE=$(curl -s -X POST http://localhost:8000/create)

echo "Response:"
echo "$RESPONSE" | python -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Check saved story
echo "[5] Checking saved story..."
ls -lh data/stories/ | tail -5
echo ""

# Show story file
if [ -f data/stories/*.json ]; then
    echo "[6] Story content:"
    cat data/stories/$(ls -t data/stories/ | head -1) | python -m json.tool | head -50
fi
echo ""

echo "==== TEST COMPLETE ===="
