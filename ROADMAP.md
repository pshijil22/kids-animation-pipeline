# Complete Development Roadmap

## Phase 1: Story Generation ✅ COMPLETE

**Goal**: Generate children's stories via local LLM

**Status**: Complete

**Deliverables**:
- Docker Compose setup (Ollama + n8n + Worker)
- Story generation via Ollama
- JSON validation
- File persistence
- FastAPI `/create` endpoint

**Test**: `./test-phase1.bat`

**Next**: Run quickstart, generate 5+ stories, verify JSON quality

---

## Phase 2: Text-to-Speech (Next)

**Goal**: Convert story narration to audio

**Components to Add**:
- eSpeak-ng system package in worker Dockerfile
- `tts.py` - eSpeak-ng wrapper
- `/speak` endpoint (takes text, returns WAV)
- Audio saved to `/data/audio/`
- Subtitle SRT generation from timing

**Files to Create**:
- Update `worker/Dockerfile` to include `espeak-ng`
- Implement `worker/tts.py`
- Add `generate_narration()` to `pipeline.py`

**Example Flow**:
```
Story JSON
  ↓
For each scene: narration text
  ↓
eSpeak-ng → WAV file
  ↓
Combine WAVs → full narration.wav
  ↓
Generate SRT (timing based on audio length)
  ↓
Save to /data/audio/
```

**Testing**:
```
POST /create → story JSON
  ↓
Check /data/audio/<job_id>.wav exists
Check /data/audio/<job_id>.srt exists
```

**Effort**: ~2 hours
**Complexity**: Low (eSpeak-ng is simple)
**Dependencies**: Only eSpeak-ng system package (free)

---

## Phase 3: Visual Generation & Video Composition

**Goal**: Create simple cartoon-style visuals + FFmpeg video

**Components to Add**:
- `scenes.py` - Generate scene images (SVG → PNG via ImageMagick or Pillow)
- `video.py` - FFmpeg video composition
- Simple scene generators:
  - Solid color backgrounds
  - Text overlays
  - Basic shapes (circles, rectangles for simple characters)
  - Pan/zoom effects in FFmpeg
- `/generate_video` endpoint

**Architecture**:
```
Story JSON
  ↓
For each scene:
  - Create background image (solid color, gradient, or basic SVG)
  - Add character shapes (simple geometric)
  - Add text overlay (scene title or narration)
  - Export as PNG
  ↓
Use FFmpeg to:
  - Read PNG sequence
  - Apply transitions (fade, slide)
  - Add pan/zoom for visual interest
  - Overlay narration audio
  - Burn subtitles
  - Output H.264 MP4 (1280×720, 30fps)
```

**Files to Create**:
- `worker/scenes.py` - Image generation
- `worker/video.py` - FFmpeg wrapper
- `templates/` - Simple SVG scene templates

**Example Scene Generation**:
```python
# Simple Python (no AI image gen yet)
from PIL import Image, ImageDraw

# Create a scene:
img = Image.new('RGB', (1280, 720), color='lightblue')
draw = ImageDraw.Draw(img)

# Draw simple shapes (character)
draw.ellipse([600, 300, 650, 400], fill='orange')  # head
draw.ellipse([580, 300, 720, 320], fill='white')   # eyes

img.save('scene_1.png')
```

**FFmpeg Integration**:
```bash
# Combine images + audio + subs
ffmpeg \
  -framerate 1/5 \
  -i "scene_%d.png" \
  -i narration.wav \
  -vf "subtitles=subtitles.srt" \
  -c:v libx264 \
  -c:a aac \
  -pix_fmt yuv420p \
  final.mp4
```

**Testing**:
```
POST /create → story JSON
  ↓
Check /data/scenes/<job_id>/ has PNG images
Check /data/videos/<job_id>.mp4 exists
Play MP4: video + narration + subtitles
```

**Effort**: ~4 hours
**Complexity**: Medium (FFmpeg integration)
**Dependencies**: FFmpeg (free), PIL/Pillow (Python)

---

## Phase 4: Music & Transitions

**Goal**: Add optional background music and improve transitions

**Components to Add**:
- Music sourcing (only royalty-free)
- Fade in/out logic
- Better transitions (cross-fade, dissolve)
- Volume mixing (music + narration balance)

**Music Sources** (all free/CC0):
- Incompetech (https://incompetech.com/)
- Free Music Archive (https://freemusicarchive.org/)
- Pixabay Music (https://pixabay.com/music/)

**FFmpeg Changes**:
```bash
ffmpeg \
  -i narration.wav \
  -i background_music.mp3 \
  -filter_complex "[1]volume=0.3[music];[0][music]amix=inputs=2:duration=first" \
  mixed_audio.wav
```

**Files to Create**:
- `worker/music.py` - Music sourcing & mixing
- `music/` directory for local music library

**Config**:
```env
ENABLE_MUSIC=true
MUSIC_DB=./music/collection.json
MUSIC_VOLUME=0.3
```

**Effort**: ~2 hours
**Complexity**: Low
**Dependencies**: FFmpeg audio filters (already included)

---

## Phase 5: n8n Automation Workflow

**Goal**: Schedule daily story generation and processing

**Components**:
- n8n workflow trigger (daily at specific time)
- Call worker `/create` endpoint
- Wait for completion
- Log results
- Handle failures

**n8n Workflow Steps**:
1. **Schedule Trigger** - Every day at 9 AM
2. **HTTP Request** - POST to worker:8000/create
3. **Wait** - For response (timeout 10 min)
4. **Error Handler** - If fails, retry 3x with exponential backoff
5. **Slack/Email Webhook** - Notify on success/failure (optional)
6. **Log Database** - Save result to local file

**n8n UI Setup** (done manually once):
1. Go to http://localhost:5678
2. Create new workflow
3. Add Schedule trigger → HTTP request → Wait → Error handler
4. Deploy and activate

**Files to Create**:
- `n8n/workflows/daily_story.json` - Exported workflow

**Effort**: ~1 hour (mostly UI clicks)
**Complexity**: Low
**Dependencies**: None (n8n already running)

---

## Phase 6: YouTube Upload Integration

**Goal**: Automatically upload finished videos to YouTube

**Components to Add**:
- OAuth 2.0 setup
- YouTube Data API v3 client
- Video upload handler
- Metadata application

**Setup** (one-time):
1. Create Google Cloud project
2. Generate OAuth 2.0 credentials
3. Authorize locally (creates refresh token)
4. Store refresh token in `/credentials/youtube_token.json`
5. Never commit token

**Files to Create**:
- `worker/youtube.py` - YouTube API wrapper
- `scripts/setup_youtube_oauth.py` - One-time OAuth setup

**Implementation**:
```python
# Initialize
youtube = build('youtube', 'v3', credentials=creds)

# Upload
body = {
    'snippet': {
        'title': metadata['title'],
        'description': metadata['description'],
        'tags': metadata['tags'],
        'categoryId': '15',  # Kids
        'madeForKids': True
    },
    'status': {
        'privacyStatus': 'private',  # Start private for testing
        'madeForKids': True
    }
}

youtube.videos().insert(
    part='snippet,status',
    body=body,
    media_body=MediaFileUpload(video_file, resumable=True)
).execute()
```

**Safety**:
- Uploads as UNLISTED/PRIVATE first
- Manual approval before public
- GENERATE_ONLY=true to skip uploads during testing

**Effort**: ~2 hours
**Complexity**: Medium (OAuth setup)
**Dependencies**: google-auth, google-auth-oauthlib (free)

---

## Phase 7: Retries, Logging, Idempotency

**Goal**: Make the pipeline robust and reliable

**Components to Add**:
- Idempotency checking (skip completed steps)
- Centralized logging (structured JSON logs)
- Retry logic with exponential backoff
- Job status tracking
- Error recovery

**Idempotency Logic**:
```python
# Before generating, check:
story_path = f"/data/stories/{job_id}_story.json"
audio_path = f"/data/audio/{job_id}.wav"
video_path = f"/data/videos/{job_id}.mp4"

# If story exists, skip generation
if exists(story_path):
    story = load(story_path)
    logger.info(f"Story already exists for {job_id}, skipping generation")
else:
    story = await generate_story_with_ollama()

# Same for audio, video, etc.
```

**Logging**:
```python
# Structured JSON logging
logger.info("story_generated", extra={
    "job_id": job_id,
    "title": story['title'],
    "scene_count": len(story['scenes']),
    "timestamp": datetime.now().isoformat(),
    "phase": 1
})
```

**Retry Strategy**:
- Phase 1 (Ollama): 3 retries, 2s exponential backoff
- Phase 2 (TTS): 2 retries, 1s backoff
- Phase 3 (Video): 1 retry, 5s backoff
- Phase 6 (YouTube): 5 retries, 10s backoff

**Files to Modify**:
- `worker/pipeline.py` - Add idempotency checks
- `worker/logging_config.py` - New logging setup
- `worker/retries.py` - New retry decorator

**Effort**: ~3 hours
**Complexity**: Medium
**Dependencies**: None

---

## Phase 8: Advanced Visuals (Optional GPU)

**Goal**: Generate more sophisticated AI-powered visuals (optional)

**Option A**: Stable Diffusion via ComfyUI (local, ~6 GB VRAM)
**Option B**: Custom cartoon style training (advanced)
**Option C**: Simple animation via OpenToonz (professional but free)

**Recommendation for V1**: Skip this unless you have GPU

**If adding later**:
1. Install ComfyUI container
2. Add `scenes.py` function to call ComfyUI API
3. Use simple prompts: "cute cartoon animal, simple style, children's book"
4. Generate scene images instead of solid colors
5. Feed to FFmpeg as before

**Effort**: ~8 hours (includes learning ComfyUI)
**Complexity**: High
**Dependencies**: GPU (NVIDIA or CPU fallback, slow)

---

## Deployment Options (Future)

### Option 1: Keep on Local PC
- Simple, no server needed
- Videos auto-generated daily
- Upload to YouTube on schedule
- Storage on PC

### Option 2: Deploy to Home Server
- Dedicated machine (NUC, Raspberry Pi, old PC)
- Always-on
- Set up SSH/VPN for remote access
- Backup to cloud

### Option 3: Lightweight Cloud Deployment
- Run on Cloud Run / AWS Lambda (Phase 3+ only, since async)
- Use external GPU for image generation
- Store videos in S3
- YouTube upload from cloud

**Recommendation**: Start with local PC (Phase 1-5), then decide.

---

## Summary Timeline

| Phase | Focus | Effort | Completion |
|-------|-------|--------|------------|
| 1 | Story gen | 2h | ✅ Done |
| 2 | TTS | 2h | ⏳ Next |
| 3 | Video | 4h | 🔜 After 2 |
| 4 | Music | 2h | 🔜 After 3 |
| 5 | n8n | 1h | 🔜 After 4 |
| 6 | YouTube | 2h | 🔜 After 5 |
| 7 | Polish | 3h | 🔜 Final |
| 8 | AI Visuals | 8h+ | 💭 Optional |

**Total for MVP**: ~16 hours of development + testing

---

## How to Proceed

### Right Now (Phase 1):
```bash
./quickstart.bat
./test-phase1.bat
```

Generate 5+ test stories.

### When Phase 1 Works:
Message me: "Phase 1 working, ready for Phase 2"

### For Each Phase:
1. I implement the phase
2. You test with provided commands
3. Iterate if issues
4. Move to next phase

---

**Welcome to building your AI video pipeline!**

Each phase is independent and builds on the previous. You can skip phases (e.g., skip music if you don't want it). Advanced phases (8) are optional.

Start with Phase 1, get it solid, then we'll build the rest together.
