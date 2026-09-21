# Kids Animation Pipeline - Ultra Simple Setup
# Run: .\start-simple.ps1

Write-Host "==== Kids Animation Pipeline - 30 Second Setup ====" -ForegroundColor Green
Write-Host ""

# Check Docker
if (!(docker --version)) {
    Write-Host "ERROR: Docker not installed" -ForegroundColor Red
    exit 1
}

# Create dirs
@('data\stories', 'data\audio', 'data\scenes', 'data\videos', 'data\logs') | ForEach-Object {
    if (!(Test-Path $_)) { New-Item -ItemType Directory -Path $_ -Force | Out-Null }
}

Write-Host "Starting services..." -ForegroundColor Cyan
docker compose down 2>&1 | Out-Null
docker compose up -d 2>&1 | Out-Null

Write-Host "Waiting 30 seconds for Ollama..." -ForegroundColor Cyan
Start-Sleep -Seconds 30

Write-Host ""
Write-Host "Downloading AI model (2.5GB, takes 5-15 min)..." -ForegroundColor Cyan
docker exec kids-channel-ollama ollama pull llama3.2:3b

Write-Host ""
Write-Host "==== READY! ====" -ForegroundColor Green
Write-Host ""
Write-Host "Generate a story:" -ForegroundColor Yellow
Write-Host ""
Write-Host "docker exec kids-channel-worker python -c `"import asyncio; from pipeline import generate_story; print(asyncio.run(generate_story()))`"" -ForegroundColor White
Write-Host ""
Write-Host "View results:" -ForegroundColor Yellow
Write-Host "  dir data\stories\" -ForegroundColor White
Write-Host ""
