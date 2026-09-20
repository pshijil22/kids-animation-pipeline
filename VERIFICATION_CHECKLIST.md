# ✅ VERIFICATION CHECKLIST

Run these commands to verify the complete pipeline works.

---

## Prerequisites ✓

- [ ] Docker Desktop installed and running
- [ ] Project directory exists with all files
- [ ] 20 GB free disk space
- [ ] 8 GB RAM minimum

**Check**:
```bash
docker --version
```

---

## Startup Phase

### 1. Start Services

```bash
docker compose up -d
```

**Expected Output**:
```
✓ kids-channel-ollama Started
✓ kids-channel-worker Started
```

- [ ] Both services started without errors

### 2. Wait for Health Checks (30-60 seconds)

```bash
docker compose ps
```

**Expected Output**:
```
CONTAINER ID   IMAGE         SERVICE   STATUS              
xxx            ollama        Healthy    
xxx            worker        Running
```

- [ ] Ollama status: `Healthy`
- [ ] Worker status: `Running`

---

## Component Verification

### 3. Verify Ollama

```bash
docker exec kids-channel-ollama ollama list
```

**Expected Output**:
```
NAME            ID              SIZE    QUANT
llama3.2:3b     xxx             2.0GB   Q4_K_M
```

- [ ] Model `llama3.2:3b` listed

If NOT listed, pull it (takes 5-10 min):
```bash
docker exec kids-channel-ollama ollama pull llama3.2:3b
```

### 4. Verify Worker Health

```bash
curl http://localhost:8000/health
```

**Expected Output**:
```json
{"status":"ok"}
```

- [ ] Returns valid JSON with `status: ok`

### 5. Verify Python Imports

```bash
docker exec kids-channel-worker python -c "from pipeline import generate_story; print('OK')"
```

**Expected Output**:
```
OK
```

- [ ] No import errors

---

## Functional Tests

### 6. Test Story Generation

```bash
docker exec kids-channel-worker python -c "from story import generate_story_with_llm; import asyncio; result = asyncio.run(generate_story_with_llm()); print(f'Title: {result.get(\"title\")}')"
```

**Expected Output**:
```
Title: <Generated Story Title>
```

- [ ] Story generated successfully
- [ ] Title contains text

### 7. Test TTS

```bash
docker exec kids-channel-worker python -c "from tts import generate_narration_from_story; import json; story = json.load(open('data/stories/'+__import__('os').listdir('data/stories/')[-1])); print(f'Scenes: {len(story.get(\"scenes\", []))}')"
```

**Expected Output**:
```
Scenes: 4
```

- [ ] Story JSON reads successfully
- [ ] Scenes count is > 0

### 8. Test Scene Generation

```bash
ls -lh data/scenes/ | grep png
```

**Expected Output**:
```
-rw-r--r--  scene_01.png  17K
-rw-r--r--  scene_02.png  16K
-rw-r--r--  scene_03.png  17K
-rw-r--r--  scene_04.png  18K
```

- [ ] PNG files exist
- [ ] Each is 15-20 KB

### 9. Test FFmpeg

```bash
docker exec kids-channel-worker ffmpeg -version | head -1
```

**Expected Output**:
```
ffmpeg version 4.x.x
```

- [ ] FFmpeg installed and runnable

---

## Full Pipeline Test

### 10. Generate Complete Video (Main Test)

```bash
docker exec kids-channel-worker python -c "import asyncio; from pipeline import generate_story; asyncio.run(generate_story())"
```

**Watch logs** (in another terminal):
```bash
docker compose logs -f worker | grep -i "step\|complete\|error"
```

**Expected**:
- Logs show "Step 1", "Step 2", etc.
- Final log: "Pipeline complete"
- Time: 3-6 minutes on CPU

- [ ] Generation completes without errors
- [ ] All phases execute

### 11. Verify Output Files

After generation completes:

```bash
ls -lh data/videos/
```

**Expected Output**:
```
total 528K
-rw-r--r--  20260919_234730.mp4  532K
```

- [ ] `.mp4` file exists
- [ ] Size is 500 KB - 1 MB
- [ ] Filename contains timestamp

### 12. Verify All Artifacts

```bash
ls -lh data/stories/ data/audio/ data/scenes/ data/videos/
```

**Expected Output** (for latest job):
```
data/stories/:
  20260919_234730_story.json        1.5K

data/audio/:
  20260919_234730_narration.wav     1.0M
  20260919_234730_subtitles.srt     546B

data/scenes/:
  20260919_234730_scene_01.png      17K
  20260919_234730_scene_02.png      16K
  20260919_234730_scene_03.png      17K
  20260919_234730_scene_04.png      18K

data/videos/:
  20260919_234730.mp4               532K
```

- [ ] Story JSON exists (1-2 KB)
- [ ] Narration WAV exists (1-1.5 MB)
- [ ] Subtitles SRT exists (500 B)
- [ ] 4 Scene PNG images exist (15-20 KB each)
- [ ] Final MP4 exists (500 KB - 1 MB)

### 13. Verify Video Quality

```bash
docker exec kids-channel-worker ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1:nokey=1 /data/videos/<latest-job>.mp4
```

Replace `<latest-job>` with actual filename from step 11.

**Expected Output**:
```
22.8
544724
```

- [ ] Duration is > 15 seconds
- [ ] Size is recorded (bytes)

### 14. Verify Video Format

```bash
docker exec kids-channel-worker ffprobe -v error -show_entries format=codec_name -of csv=p=0 /data/videos/<latest-job>.mp4
```

**Expected Output**:
```
h264,aac
```

- [ ] Video codec is `h264` (or h264/hevc)
- [ ] Audio codec is `aac` (or mp3)

---

## Optional: YouTube Setup

### 15. Check YouTube Module

```bash
docker exec kids-channel-worker python -c "from youtube import upload_to_youtube; print('YouTube module OK')"
```

**Expected Output**:
```
YouTube module OK
```

- [ ] No import errors

### 16. Generate with Upload (if configured)

If you've set up OAuth credentials:

```bash
# Check GENERATE_ONLY setting
docker exec kids-channel-worker grep GENERATE_ONLY .env
```

If `GENERATE_ONLY=false`, next video generation will attempt upload.

- [ ] GENERATE_ONLY is understood (true = skip upload)

---

## Final Verification

### 17. Run Full Test Suite

```bash
bash test_pipeline.sh
```

**Expected Output**:
```
✓ PASS - Multiple test results
```

- [ ] Most tests pass
- [ ] Any failures are documented

### 18. Clean Logs Check

```bash
docker compose logs worker | tail -20
```

**Expected**: Recent logs showing recent generation activity, no error spam.

- [ ] No repeated error messages
- [ ] Timestamps are recent

---

## Summary Checklist

**Infrastructure**:
- [ ] Docker Compose services running
- [ ] Ollama model available
- [ ] Worker health OK

**Components**:
- [ ] Python modules import correctly
- [ ] FFmpeg available
- [ ] Directories exist

**Functionality**:
- [ ] Story generation works
- [ ] TTS audio created
- [ ] Scene images generated
- [ ] Video composed successfully
- [ ] All output files exist
- [ ] Video format is correct

**Quality**:
- [ ] Video duration > 15 sec
- [ ] File size reasonable (500 KB - 1 MB)
- [ ] Codecs are H.264 + AAC
- [ ] No persistent errors

---

## ✅ PASSING CRITERIA

You pass if:

✅ All 18 checkboxes above are checked  
✅ Final MP4 video exists and is playable  
✅ All phases complete without errors  
✅ Output files are in expected locations  
✅ Generation time is 3-6 minutes  

---

## 🎬 SUCCESS!

If you checked all boxes above, your kids animation pipeline is **fully operational** and ready to generate videos.

**Next**: Generate more videos, tweak settings, or set up YouTube upload!

```bash
docker exec kids-channel-worker python -c "import asyncio; from pipeline import generate_story; asyncio.run(generate_story())"
```

---

## 🐛 Troubleshooting

If any box is unchecked, see **TESTING_GUIDE.md** for detailed debugging steps.

Common issues:
- **Services won't start**: Check `docker compose logs` for errors
- **Model not found**: Run `ollama pull llama3.2:3b` (one-time, 10 min)
- **Generation hangs**: Normal on CPU, wait 5+ minutes or check `docker compose logs ollama`
- **Out of memory**: Increase Docker RAM or use smaller model
- **FFmpeg errors**: Rebuild worker: `docker compose build worker --no-cache`

---

**Happy video generation! 🎬**
