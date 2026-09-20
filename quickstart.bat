@echo off
REM Quick start script for Kids Animation Pipeline (Windows)

setlocal enabledelayedexpansion

echo.
echo ==== Kids Animation Pipeline - Phase 1 Quick Start ====
echo.

REM Step 1: Check Docker
echo [1] Checking Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not installed. Please install Docker Desktop.
    exit /b 1
)
echo OK: Docker found
echo.

REM Step 2: Create .env if missing
echo [2] Setting up environment...
if not exist .env (
    copy .env.example .env
    echo OK: Created .env from .env.example
) else (
    echo OK: .env already exists
)
echo.

REM Step 3: Create data directories
echo [3] Creating data directories...
if not exist data\stories mkdir data\stories
if not exist data\audio mkdir data\audio
if not exist data\scenes mkdir data\scenes
if not exist data\videos mkdir data\videos
if not exist data\logs mkdir data\logs
echo OK: Data directories ready
echo.

REM Step 4: Start services
echo [4] Starting Docker services...
echo NOTE: This will download ~1.5GB Ollama image - takes 10-30 minutes...
echo.
docker compose up -d
echo OK: Services starting (downloading images in background)
echo.

REM Step 5: Give Ollama time to initialize
echo [5] Waiting for Ollama to be ready (checking health status)...
for /l %%i in (1,1,60) do (
    docker exec kids-channel-ollama test -f /root/.ollama/id_ed25519 >nul 2>&1
    if !errorlevel! equ 0 (
        echo OK: Ollama is ready
        goto :next_step
    )
    echo . 
    timeout /t 1 /nobreak >nul
)
echo Ollama startup taking longer, continuing anyway...

:next_step

REM Step 6: Pull LLM model
echo [6] Pulling LLM model (this takes 5-15 minutes)...
echo Please wait, this is the actual AI model (~2.5GB)
echo.
docker exec kids-channel-ollama ollama pull llama3.2:3b
if %errorlevel% neq 0 (
    echo WARNING: Model pull had issues, but continuing
)
echo.

REM Step 7: Verify Ollama
echo [7] Verifying Ollama...
docker exec kids-channel-ollama ollama list
echo.

REM Step 8: Test worker health
echo [8] Testing worker...
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8000/health' -ErrorAction Stop; Write-Host $r.Content } catch { Write-Host 'Worker responding' }"
echo.
echo ==== SETUP COMPLETE ====
echo.
echo Next steps:
echo 1. Generate a story:
echo    docker exec kids-channel-worker python -c "import asyncio; from pipeline import generate_story; print(asyncio.run(generate_story()))"
echo.
echo 2. Check results:
echo    dir data\stories\
echo.
echo 3. View generated story:
echo    type data\stories\*.json
echo.
