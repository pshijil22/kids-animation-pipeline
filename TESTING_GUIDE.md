# 🧪 Testing Guide - Kids Animation Pipeline

**Status**: Complete pipeline tested ✅ **WORKING**

---

## Quick Test (Copy & Paste)

### 1. Start the System

```bash
docker compose up -d
```

Wait 10-15 seconds for services to become healthy.

### 2. Verify Services Are Running

```bash
docker compose ps
```

You should see:
- `kids-channel-ollama` - Healthy
- `kids-channel-worker` - Running

### 3. Check Ollama Model Is Available

```bash
docker exec kids-channel-ollama ollama list
```

You should see `llama3.2:3b` listed.

If NOT listed, pull it:
```bash
docker exec kids-channel-ollama ollama pull llama3.2:3b
```

(Takes 5-10 minutes)

### 4. Test Worker Health

```bash
curl http://localhost:8000/health
```

Response:
```json
{"status":"ok"}
```

### 5. **Generate Your First Video** (Main Test)

```bash
docker exec kids-channel-worker python -c "import asyncio; from pipeline import generate_story; asyncio.run(generate_story())"
```

**Expected time**: 3-6 minutes on CPU-only (depends on your hardware)

**Watch logs** (in another terminal):
```bash
docker compose logs -f worker
```

### 6. Verify Output Files

Once complete, check what was generated:

```bash
# View video file
ls -lh data/videos/

# View story JSON
ls -lh data/stories/

# View audio files
ls -lh data/audio/

# View scene images
ls -lh data/scenes/
```

You should see:
```
data/videos/20260919_234730.mp4            532 KB   ← Final video
data/stories/20260919_234730_story.json    1.5 KB   ← Story
data/audio/20260919_234730_narration.wav   1.0 MB   ← Audio
data/audio/20260919_234730_subtitles.srt   546 B    ← Subtitles
data/scenes/20260919_234730_scene_01.png   17.6 KB  ← Scene images (4 total)
data/scenes/20260919_234730_scene_02.png   15.7 KB
data/scenes/20260919_234730_scene_03.png   16.8 KB
data/scenes/20260919_234730_scene_04.png   18.4 KB
```

### 7. Check Video Quality

```bash
# Get video info
docker exec kids-channel-worker ffprobe -v error \
  -show_entries format=duration,size \
  -of default=noprint_wrappers=1:nokey=1 \
  /data/videos/20260919_234730.mp4
```

Output (example):
```
22.8         ← Duration in seconds
544724       ← Size in bytes (532 KB)
```

---

## Full Test Checklist

Run through this to verify ALL components work:

- [ ] **Docker Compose services start**
  ```bash
  docker compose ps
  ```
  Result: All services `healthy` or `running`

- [ ] **Ollama model is available**
  ```bash
  docker exec kids-channel-ollama ollama list | grep llama3.2:3b
  ```
  Result: Model listed

- [ ] **Worker is healthy**
  ```bash
  curl http://localhost:8000/health
  ```
  Result: `{"status":"ok"}`

- [ ] **Worker can import modules**
  ```bash
  docker exec kids-channel-worker python -c "from pipeline import generate_story; print('OK')"
  ```
  Result: `OK`

- [ ] **Story generation completes**
  ```bash
  docker exec kids-channel-worker python -c \
    "import asyncio; from pipeline import generate_story; result = asyncio.run(generate_story()); print(f'Generated: {result[\"title\"]}')"
  ```
  Result: `Generated: <story title>`
  Time: 2-5 minutes

- [ ] **Story JSON is valid**
  ```bash
  docker exec kids-channel-worker python -c \
    "import json; f = open('/data/stories/' + __import__('os').listdir('/data/stories/')[-1]); print(json.dumps(json.load(f), indent=2)[:200])"
  ```
  Result: Valid JSON with `title`, `scenes`, etc.

- [ ] **Narration audio exists**
  ```bash
  ls -lh data/audio/*narration.wav
  ```
  Result: File listed (1-1.5 MB)

- [ ] **Scene images exist**
  ```bash
  ls -lh data/scenes/*.png | wc -l
  ```
  Result: Number of PNG files (should be 4+)

- [ ] **Final MP4 video exists**
  ```bash
  ls -lh data/videos/*.mp4
  ```
  Result: File listed (500 KB - 1 MB)

- [ ] **Subtitles exist**
  ```bash
  ls -lh data/audio/*.srt
  ```
  Result: SRT file listed

---

## Detailed Output Example

When you run the generation command, you'll see logs like:

```
worker_1  | 2026-09-19 23:47:30,123 - pipeline - INFO - Starting story generation job: 20260919_234730
worker_1  | 2026-09-19 23:47:30,456 - story - INFO - Step 1: Calling Ollama LLM
worker_1  | 2026-09-19 23:47:30,789 - story - INFO - LLM generation successful
worker_1  | 2026-09-19 23:47:31,012 - story - INFO - Story validated: 'Bella's Magical Adventure'
worker_1  | 2026-09-19 23:47:31,234 - pipeline - INFO - Step 2: Saving story to disk
worker_1  | 2026-09-19 23:47:31,456 - pipeline - INFO - Step 3: Generating narration audio
worker_1  | 2026-09-19 23:47:31,678 - tts - INFO - Generating audio for scene 1...
worker_1  | 2026-09-19 23:48:12,901 - tts - INFO - Generated 4 scene images
worker_1  | 2026-09-19 23:48:13,234 - video - INFO - Running FFmpeg...
worker_1  | 2026-09-19 23:48:45,567 - video - INFO - Video created successfully
worker_1  | 2026-09-19 23:48:45,890 - youtube - INFO - GENERATE_ONLY=true, skipping YouTube upload
worker_1  | 2026-09-19 23:48:46,123 - pipeline - INFO - Pipeline complete: story + narration + video generated
```

---

## Test Results Summary

### Generated Artifacts

| Component | File | Size | Status |
|-----------|------|------|--------|
| Story | `{job_id}_story.json` | 1-2 KB | ✅ JSON |
| Scene 1 | `{job_id}_scene_01.png` | 15-20 KB | ✅ PNG |
| Scene 2 | `{job_id}_scene_02.png` | 15-20 KB | ✅ PNG |
| Scene 3 | `{job_id}_scene_03.png` | 15-20 KB | ✅ PNG |
| Scene 4 | `{job_id}_scene_04.png` | 15-20 KB | ✅ PNG |
| Narration | `{job_id}_narration.wav` | 1-1.5 MB | ✅ WAV |
| Subtitles | `{job_id}_subtitles.srt` | 500 B | ✅ SRT |
| **Final Video** | **`{job_id}.mp4`** | **500 KB - 1 MB** | **✅ H.264+AAC** |

### Performance Metrics

| Metric | Value | Note |
|--------|-------|------|
| Story Generation | 1-3 min | Ollama LLM on CPU |
| TTS (4 scenes) | 20-40 sec | eSpeak-ng |
| Scene Generation | 1 sec | Pillow |
| FFmpeg Composition | 10-20 sec | Encoding MP4 |
| **Total Time** | **3-6 minutes** | CPU-only |
| **With GPU** | **30-90 sec** | NVIDIA CUDA |

### Video Quality

- **Resolution**: 1280×720 (HD)
- **Codec**: H.264 (YouTube-compatible)
- **Audio**: AAC 128 kbps
- **FPS**: 30 fps
- **Subtitles**: Burned-in SRT
- **Duration**: Dynamic (based on narration)

---

## Common Issues & Fixes

### "Ollama connection refused"

```bash
docker compose restart ollama
docker logs ollama
# Wait 30 seconds, then test again
curl http://localhost:11434/api/tags
```

### "Generation hangs for >10 min"

Normal on CPU. Ollama needs 2-5 minutes to generate text.

Monitor:
```bash
docker compose logs -f ollama
```

Interrupt and retry:
```bash
docker exec kids-channel-worker python -c "import signal; signal.SIGTERM"
```

### "Worker crashes"

```bash
docker logs kids-channel-worker
```

Check for:
- Missing imports → rebuild: `docker compose build worker`
- Out of memory → increase Docker RAM
- Ollama timeout → increase timeout in `story.py`

### "Video is black or has no audio"

Check FFmpeg input files exist:
```bash
ls data/scenes/{job_id}*
ls data/audio/{job_id}_narration.wav
ls data/audio/{job_id}_subtitles.srt
```

If missing, check worker logs for the specific failure stage.

---

## Test Success Criteria

✅ **Phase 1 Success**: Story JSON is valid and saved  
✅ **Phase 2 Success**: WAV and SRT files exist  
✅ **Phase 3 Success**: PNG scene images exist  
✅ **Phase 3 Success**: Final MP4 is playable and has audio  
✅ **Overall Success**: All 5 checks pass

---

## Next Steps After Successful Test

1. **Generate more videos** to verify consistency
2. **Tweak parameters** in `.env` if needed (model, bitrate, FPS)
3. **Set up YouTube OAuth** (optional)
4. **Configure n8n** for daily scheduling (Phase 5)
5. **Upgrade visuals** with ComfyUI (Phase 8, optional)

---

**Your pipeline is fully functional. Run a generation and check the output files!**
