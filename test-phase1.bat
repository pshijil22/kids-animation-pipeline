@echo off
REM Test script for Phase 1: Story Generation (Windows)

echo.
echo ==== Testing Kids Animation Pipeline - Phase 1 ====
echo.

REM Check if services are running
echo [1] Checking services...
docker compose ps
echo.

REM Check Ollama
echo [2] Testing Ollama connection...
docker exec kids-channel-ollama ollama list
echo.

REM Check worker health
echo [3] Testing worker health...
powershell -Command "(Invoke-WebRequest -Uri 'http://localhost:8000/health').Content"
echo.

REM Generate a story
echo [4] Generating a test story...
echo (This may take 1-2 minutes on CPU-only systems)
echo.

powershell -Command "Invoke-WebRequest -Uri 'http://localhost:8000/create' -Method Post | Select-Object -ExpandProperty Content | ConvertFrom-Json | ConvertTo-Json"
echo.

REM Check saved story
echo [5] Checking saved story...
dir data\stories\
echo.

echo ==== TEST COMPLETE ====
echo.
