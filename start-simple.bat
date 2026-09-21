@echo off
REM Kids Animation Pipeline - Ultra-Fast Setup
REM This is the SIMPLEST possible setup

echo.
echo ==== Kids Animation Pipeline - 30 Second Setup ====
echo.

REM Check Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker Desktop not running. Please start it and try again.
    exit /b 1
)

REM Create data dirs
if not exist data\stories mkdir data\stories
if not exist data\audio mkdir data\audio
if not exist data\scenes mkdir data\scenes
if not exist data\videos mkdir data\videos
if not exist data\logs mkdir data\logs

REM Start
echo Starting services...
docker compose down >nul 2>&1
docker compose up -d

REM Wait for ready
echo.
echo Waiting for Ollama...
timeout /t 30 /nobreak

REM Pull model
echo.
echo Downloading AI model (2.5GB, takes 5-15 min)...
docker exec kids-channel-ollama ollama pull llama3.2:3b

REM Done
echo.
echo ==== READY! ====
echo.
echo Generate a story:
echo.
echo docker exec kids-channel-worker python -c "import asyncio; from pipeline import generate_story; print(asyncio.run(generate_story()))"
echo.
echo View results:
echo   dir data\stories\
echo.
