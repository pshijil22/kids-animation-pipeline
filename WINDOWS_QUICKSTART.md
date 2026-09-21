# Windows Quick Start (5 Minutes)

This is the fastest way to get started on Windows.

## Prerequisites

✅ Docker Desktop installed?
```powershell
docker --version
```

If you see version number: Great! Skip to "Step 1" below.

If not: Download and install from https://www.docker.com/products/docker-desktop

---

## Step-by-Step

### Step 1: Open PowerShell

**Click Start**, type `PowerShell`, right-click → **Run as Administrator**

### Step 2: Navigate to project folder

```powershell
cd path\to\kids-channel
```

(Replace with actual path to your project)

### Step 3: Run ONE command

```powershell
.\quickstart.bat
```

**This automatically:**
- Creates `.env`
- Starts Ollama, n8n, Worker
- Downloads the AI model (~2.5 GB, 5-10 minutes)
- Tests everything

When done, you'll see:
```
==== SETUP COMPLETE ====

Next steps:
1. Monitor logs: docker compose logs -f worker
2. Generate a story: curl -X POST http://localhost:8000/create
3. Check results: dir /s data\stories\
4. Open n8n UI: http://localhost:5678
```

### Step 4: Generate your first story

In PowerShell, run:

```powershell
Invoke-WebRequest -Uri "http://localhost:8000/create" -Method Post | Select-Object -ExpandProperty Content | ConvertFrom-Json | ConvertTo-Json | Out-Host
```

**What to expect:**
- Takes 1-5 minutes (CPU generates text)
- Returns a story in JSON format
- Check `data\stories\` folder for the saved file

### Step 5: Verify

```powershell
ls data\stories\
Get-Content data\stories\<filename>.json
```

You should see a JSON file with a children's story.

---

## Troubleshooting

### "Command not found: .\quickstart.bat"

Your PowerShell execution policy may be restricted. Run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then retry: `.\quickstart.bat`

### "docker: command not found"

Docker Desktop is not installed or not in PATH.

1. Open Docker Desktop from Start menu
2. Wait for it to start
3. Retry: `docker --version`

### "port 8000 already in use"

Another service is using port 8000.

Either:
- Stop that service
- Or change in `.env`: `WORKER_PORT=8001`

### Script hangs during "Pulling model"

Ollama is downloading (~2.5 GB). This is normal. Be patient (5-10 min).

Watch progress:
```powershell
docker logs -f kids-channel-ollama
```

### Story generation times out

On CPU-only, stories take 1-3 minutes. This is normal.

If it takes longer than 10 minutes:
```powershell
docker logs -f kids-channel-worker
```

Look for errors or use a smaller model:
```powershell
docker exec kids-channel-ollama ollama pull tinyllama:latest
```

Update `.env`:
```
OLLAMA_MODEL=tinyllama:latest
docker compose restart worker
```

---

## Common Commands

### View logs

```powershell
# All services
docker compose logs -f

# Just worker (story generation)
docker compose logs -f worker

# Just Ollama (LLM)
docker compose logs -f ollama

# Just n8n
docker compose logs -f n8n
```

Press `Ctrl+C` to stop viewing.

### Stop everything

```powershell
docker compose down
```

Data is saved. Restart with:
```powershell
docker compose up -d
```

### Generate another story

```powershell
Invoke-WebRequest -Uri "http://localhost:8000/create" -Method Post | Select-Object -ExpandProperty Content
```

### Check all running containers

```powershell
docker ps
```

You should see:
- kids-channel-ollama
- kids-channel-worker
- kids-channel-n8n

---

## Next Steps (After Phase 1 Works)

1. **Generate 5+ test stories**
   - Command: Repeat the generation command above
   - Check quality and JSON structure

2. **Monitor logs for issues**
   - Command: `docker compose logs -f worker`

3. **Verify file saving**
   - Command: `ls data\stories\`

4. **When Phase 1 is solid**, message me for Phase 2

---

## URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Worker API | http://localhost:8000 | Story generation |
| n8n | http://localhost:5678 | Workflow UI (Phase 5) |
| Ollama | http://localhost:11434 | LLM (backend, no UI) |

---

## Key Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | All services defined |
| `.env` | Your configuration |
| `worker/story.py` | Story generation logic |
| `prompts/story.txt` | AI prompt |
| `data/stories/` | Generated stories (saved here) |
| `SETUP_GUIDE.md` | Detailed setup guide |
| `PHASE1_SUMMARY.md` | What's been built |
| `ROADMAP.md` | Future phases |

---

## Tips for Beginners

1. **Docker takes time to start**
   - First `docker compose up -d` takes 30+ seconds
   - Be patient

2. **Ollama is slow on CPU**
   - Story generation: 1-5 minutes normal
   - GPU would be 10x faster
   - Consider running overnight

3. **Check logs first**
   - Most errors are in logs
   - Command: `docker logs kids-channel-worker-1`

4. **PowerShell vs Command Prompt**
   - Either works
   - PowerShell recommended (better output)

5. **JSON responses are your friend**
   - Each story returns structured JSON
   - Phase 2 will parse this for TTS
   - Phase 3 will render visuals from it

---

## You're All Set!

🎉 Run the quickstart:

```powershell
.\quickstart.bat
```

Let me know when Phase 1 is working and you're ready for Phase 2!
