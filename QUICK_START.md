# 🚀 QUICK START - 5 Minutes to Your First Video

## Step 1: Start Services (30 seconds)

```bash
docker compose up -d
```

Verify:
```bash
docker compose ps
# Should show: ollama (Healthy), worker (Running)
```

## Step 2: Pull Model (if first time, 5-10 min)

```bash
docker exec kids-channel-ollama ollama list
```

If `llama3.2:3b` is NOT listed:
```bash
docker exec kids-channel-ollama ollama pull llama3.2:3b
```

## Step 3: Generate Your First Video (3-6 minutes)

```bash
docker exec kids-channel-worker python -c "import asyncio; from pipeline import generate_story; asyncio.run(generate_story())"
```

Watch the magic happen:
```bash
docker compose logs -f worker
```

## Step 4: Check Your Video ✅

Once done (watch for "Pipeline complete" in logs):

```bash
# See the final MP4
ls -lh data/videos/*.mp4

# See story JSON
cat data/stories/*.json | jq .title

# Verify video info
docker exec kids-channel-worker ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1:nokey=1 /data/videos/*.mp4
```

## Result

You'll have:
- 📝 Story JSON
- 🎤 Narration audio (WAV)
- 📝 Subtitles (SRT)
- 🖼️ Scene images (PNG × 4)
- 🎬 **Final MP4 video** ← Ready for YouTube!

---

## 🎉 DONE! 

Your kids animation pipeline just generated a complete video from scratch.

Generate more:
```bash
docker exec kids-channel-worker python -c "import asyncio; from pipeline import generate_story; asyncio.run(generate_story())"
```

Upload to YouTube (optional):
1. Set up OAuth (see FINAL_README.md)
2. Change `GENERATE_ONLY=false` in `.env`
3. Videos auto-upload on next generation

---

**For full documentation**: See `FINAL_README.md` and `TESTING_GUIDE.md`
