# CRITICAL: Phase 1 First-Run Instructions

## The Situation

You ran `quickstart.bat` and hit the **n8n image pull error**. This is because n8n has authentication issues on some networks (not critical for Phase 1).

**Good news**: We've removed n8n from Phase 1. It's not needed yet (Phase 5). Just Ollama + Worker.

## What's Happening Now

The Docker images are **downloading in the background**:
- Ollama container: ~1.5 GB (downloading now, takes 10-30 min depending on internet)
- Worker image: Already built locally ✓

This is completely normal. Large images take time.

## Wait for Images to Pull

**Do NOT stop the download.** Let it complete. Check progress:

```powershell
# In a new PowerShell window
docker ps -a
```

Look for:
```
STATUS: Pulling fs layer
```

or

```
STATUS: Up X minutes
```

When you see `STATUS: Up`, it's ready.

## Once Running (After images pull)

Once Ollama and Worker are running, pull the LLM model:

```powershell
docker exec kids-channel-ollama ollama pull llama3.2:3b
```

This is the **actual model** (~2.5 GB). The first time takes 5-15 minutes.

## Then Generate a Story

```powershell
Invoke-WebRequest -Uri "http://localhost:8000/create" -Method Post | Select-Object -ExpandProperty Content | ConvertFrom-Json | ConvertTo-Json | Out-Host
```

## Timeline

| Step | Time | Status |
|------|------|--------|
| Docker image pull | 10-30 min | ⏳ Happening now |
| LLM model download | 5-15 min | ⏳ After images ready |
| Story generation | 1-5 min | ⏳ After model ready |
| **Total** | **20-50 min** | — |

**Just wait. Everything is automated.**

---

## If You Want to Monitor

```powershell
# Watch the background job
docker logs -f kids-channel-ollama
docker logs -f kids-channel-worker
```

---

## What Was Changed

- ✅ Removed n8n from docker-compose (not needed for Phase 1, added in Phase 5)
- ✅ Now just 2 services: Ollama + Worker
- ✅ Simplified and faster startup
- ✅ Same Phase 1 story generation

---

## Go Get Coffee ☕

Let the downloads finish. Come back in 30 minutes.
