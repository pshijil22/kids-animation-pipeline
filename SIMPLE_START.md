# 🚀 Super Simple Start (No More Waiting Issues)

## The Problem

The old `quickstart.bat` had a broken waiting loop that kept printing "... still waiting" forever.

## The Solution

Two new ultra-simple scripts that **just work**:

### Option 1: Batch Script (Simplest)

```powershell
.\start-simple.bat
```

That's it. No loops, no confusion. Runs:
1. Stops old containers
2. Starts new ones
3. Waits 30 seconds
4. Pulls model
5. Done

### Option 2: PowerShell Script (Colored output)

```powershell
.\start-simple.ps1
```

Same thing, but with nice colored text.

### Option 3: Manual Commands (You control everything)

```powershell
# 1. Start services
docker compose up -d

# 2. Wait 30 seconds
Start-Sleep -Seconds 30

# 3. Pull model
docker exec kids-channel-ollama ollama pull llama3.2:3b

# 4. Generate story
docker exec kids-channel-worker python -c "import asyncio; from pipeline import generate_story; print(asyncio.run(generate_story()))"

# 5. Check results
dir data\stories\
```

---

## Total Time

- **First run**: 20-50 minutes (image download + model pull)
- **Subsequent runs**: 1-5 minutes per story

---

## What Each Script Does

| File | Complexity | Output |
|------|-----------|--------|
| `start-simple.bat` | Minimal | Plain text |
| `start-simple.ps1` | Minimal | Colored text |
| `quickstart.bat` | Detailed | Verbose (old, has issues) |
| Manual commands | Full control | Exactly what you want |

---

## Generate a Story

Once setup completes, generate stories anytime:

```powershell
docker exec kids-channel-worker python -c "import asyncio; from pipeline import generate_story; print(asyncio.run(generate_story()))"
```

Stories save to: `data/stories/`

---

## View Results

```powershell
# List all stories
dir data\stories\

# View latest story
Get-Content (Get-ChildItem data\stories\ | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Select-Object -ExpandProperty FullName) | ConvertFrom-Json | ConvertTo-Json
```

---

## Stop Everything

```powershell
docker compose down
```

---

## That's It

Use `start-simple.bat` or `start-simple.ps1`. No more broken loops. Clean and fast.

When setup is done, just generate stories and enjoy! 🎉
