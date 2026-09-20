# Kids Animation Pipeline - Phase 1 Setup Guide

**Status**: Phase 1 Complete - Story generation via Ollama LLM  
**Target**: Generate original children's stories locally

---

## What You Have

A complete Docker-based system with:
- **Ollama** - Local LLM backend (runs the AI)
- **n8n** - Workflow orchestration (will automate in Phase 5)
- **Python Worker** - FastAPI service that calls Ollama and saves stories
- **Persistent volumes** - Stories saved to disk

All services are containerized, auto-restart on failure, and have health checks.

---

## Installation (First Time Only)

### Windows Setup

**Requirements:**
- Docker Desktop (with WSL 2 backend)
- PowerShell or Command Prompt

**Steps:**

1. **Install Docker Desktop**
   - Download: https://www.docker.com/products/docker-desktop
   - Run the installer
   - Restart your computer
   - Verify: Open PowerShell and run `docker --version`

2. **Clone or download this project**
   ```powershell
   git clone <your-repo-url>
   cd kids-channel
   ```

3. **Create environment file**
   ```powershell
   copy .env.example .env
   ```

4. **Run quickstart**
   ```powershell
   .\quickstart.bat
   ```

   This automatically:
   - Verifies Docker is installed
   - Creates data directories
   - Starts all services (Ollama, n8n, worker)
   - Pulls the LLM model (~2.5 GB, takes 5–10 min)
   - Verifies everything works

5. **Wait for completion**
   - The script runs for 5–15 minutes
   - Watch the output for errors
   - When done, you'll see "SETUP COMPLETE"

### macOS/Linux Setup

1. **Install Docker Desktop** - https://www.docker.com/products/docker-desktop

2. **Clone project**
   ```bash
   git clone <your-repo-url>
   cd kids-channel
   ```

3. **Create environment**
   ```bash
   cp .env.example .env
   ```

4. **Run quickstart**
   ```bash
   bash quickstart.sh
   ```

---

## Verify Everything Works

### Run the Test Suite

**Windows:**
```powershell
.\test-phase1.bat
```

**macOS/Linux:**
```bash
bash test-phase1.sh
```

This tests:
1. Docker services are running
2. Ollama is accessible
3. Worker is healthy
4. Story generation works
5. Files are saved correctly

Expected output:
```
[1] Checking services...
[2] Testing Ollama connection...
[3] Testing worker health...
[4] Generating a test story...
[5] Checking saved story...
==== TEST COMPLETE ====
```

---

## Generate Your First Story

### Manual Generation (Command Line)

**Windows PowerShell:**
```powershell
$response = Invoke-WebRequest -Uri "http://localhost:8000/create" -Method Post
$response.Content | ConvertFrom-Json | ConvertTo-Json
```

**macOS/Linux Bash:**
```bash
curl -X POST http://localhost:8000/create | python -m json.tool
```

### Expected Response

The worker will return JSON like:

```json
{
  "title": "Bella the Brave Little Deer",
  "description": "A young deer learns that courage comes in many forms",
  "lesson": "Being brave doesn't mean being fearless; it means doing what's right despite being scared",
  "age_range": "4-8",
  "scenes": [
    {
      "number": 1,
      "title": "The Quiet Forest",
      "narration": "In a quiet forest where tall green trees grew...",
      "visual_description": "A peaceful forest with soft sunlight filtering through leaves...",
      "duration_seconds": 15
    },
    ...
  ],
  "job_id": "20260919_123456",
  "saved_path": "/data/stories/20260919_123456_story.json"
}
```

### View Generated Stories

**Windows:**
```powershell
ls data\stories\
Get-Content data\stories\<filename>.json | ConvertFrom-Json | ConvertTo-Json
```

**macOS/Linux:**
```bash
ls -la data/stories/
cat data/stories/<filename>.json | python -m json.tool
```

---

## Monitor Logs

### Watch Live Logs

**All services:**
```
docker compose logs -f
```

**Just the worker:**
```
docker compose logs -f worker
```

**Just Ollama:**
```
docker compose logs -f ollama
```

**Just n8n:**
```
docker compose logs -f n8n
```

Press `Ctrl+C` to stop viewing logs.

### Common Log Messages

✓ **Good sign:**
```
worker_1  | Story validated: 'Bella the Brave Little Deer'
worker_1  | Story saved to: /data/stories/20260919_123456_story.json
```

❌ **Problem - Ollama not ready:**
```
worker_1  | Ollama not ready, retrying in 1s (attempt 1/30)
```
→ Wait longer or check `docker logs ollama`

❌ **Problem - Model not found:**
```
ollama_1  | could not run model
```
→ Run: `docker exec kids-channel-ollama ollama pull llama3.2:3b`

❌ **Problem - Hang during generation:**
```
# (No output for 1+ minutes)
```
→ Ollama is thinking. On CPU-only, this takes 1–3 minutes. Be patient.

---

## Troubleshooting

### Services won't start

**Check if Docker daemon is running:**

Windows: Open Docker Desktop app from Start menu.

macOS/Linux: `docker ps` should succeed.

### Worker crashes

```
docker logs kids-channel-worker-1
```

Look for Python errors. Most likely: Ollama not ready yet.

### Ollama says "connection refused"

```
docker compose restart ollama
docker logs ollama
```

Wait 30 seconds, then test:
```
docker exec kids-channel-ollama ollama list
```

### Model download fails (no internet, timeout)

```
docker exec kids-channel-ollama ollama pull llama3.2:3b
```

If it times out, try a smaller model:
```
docker exec kids-channel-ollama ollama pull tinyllama:latest
```

Then update `.env`:
```
OLLAMA_MODEL=tinyllama:latest
docker compose restart worker
```

### Story generation times out (hangs for 10+ minutes)

This is expected on CPU-only hardware for the first run. Ollama is slow without GPU.

- **GPU accelerated (NVIDIA)**: 30–60 seconds
- **CPU only**: 2–5 minutes per story

Consider:
1. Running overnight on slower hardware
2. Using a smaller model (tinyllama instead of llama3.2)
3. Adding a GPU (Phase 8 can leverage CUDA)

### Disk space issue

Check available space:

**Windows:**
```powershell
Get-PSDrive C
```

**macOS/Linux:**
```bash
df -h
```

Ollama models need 3–5 GB. Ensure you have 10+ GB free.

---

## System Resource Requirements

### Minimum (Slow but works)

- **CPU**: Any modern processor (4+ cores recommended)
- **RAM**: 8 GB (4 GB minimum)
- **Disk**: 20 GB free (Ollama + Docker images)
- **Network**: For initial model download (5–10 MB/s)

### Recommended

- **CPU**: 8+ cores
- **RAM**: 16 GB
- **Disk**: 50 GB free
- **GPU**: NVIDIA (optional, speeds up 10x)

### GPU Support (Optional for Phase 3+)

If you have NVIDIA GPU:

1. Install NVIDIA Docker runtime
2. Uncomment in docker-compose.yml: `deploy: resources: reservations: devices: - driver: nvidia`
3. Ollama will auto-detect and use GPU

Without GPU, everything still works—just slower.

---

## How to Stop / Restart Services

### Stop Everything

```
docker compose down
```

Data is preserved. Restart with:
```
docker compose up -d
```

### Stop One Service

```
docker compose stop worker
docker compose stop ollama
docker compose stop n8n
```

### Restart One Service

```
docker compose restart worker
```

### Reset Everything (WARNING: Deletes data!)

```
docker compose down -v
```

This deletes generated stories, Ollama cache, n8n data. Only do if you want a clean slate.

---

## Next Steps (When Ready)

Phase 2 will add:
- Local text-to-speech (eSpeak-ng)
- Save narration audio
- Subtitle generation

Phase 3 will add:
- Simple scene images (SVG + PNG)
- FFmpeg video composition
- Final MP4 output

---

## How to Get Help

1. **Check logs first**
   ```
   docker compose logs worker
   ```

2. **Run test suite**
   ```
   test-phase1.bat  (Windows)
   bash test-phase1.sh  (macOS/Linux)
   ```

3. **Verify Docker is installed**
   ```
   docker --version
   docker compose version
   ```

4. **Verify services are running**
   ```
   docker ps
   ```

5. **Check network connectivity**
   ```
   docker exec kids-channel-worker curl http://ollama:11434/api/tags
   ```

---

## Key Files

- `docker-compose.yml` - All services defined here
- `.env` - Your configuration (copy from `.env.example`)
- `worker/app.py` - FastAPI server
- `worker/story.py` - Story generation logic
- `prompts/story.txt` - LLM prompt
- `data/stories/` - Generated story JSON files
- `quickstart.bat/sh` - One-command setup

---

## Architecture Diagram

```
                          ┌─────────────┐
                          │  n8n (UI)   │
                          │  :5678      │
                          └─────────────┘
                                 ↑
                                 │
                    ┌────────────┴────────────┐
                    │                         │
              ┌─────▼────────┐        ┌──────▼──────┐
              │   Worker     │        │   Ollama    │
              │  (FastAPI)   │◄──────►│   (LLM)     │
              │   :8000      │        │   :11434    │
              └──────────────┘        └─────────────┘
                    │
                    │ saves JSON
                    ▼
            ┌─────────────────┐
            │ data/stories/   │
            │ story_*.json    │
            └─────────────────┘
```

---

**You're ready to generate stories! Run `./quickstart.bat` and let me know if you hit any issues.**
