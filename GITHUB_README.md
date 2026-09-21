# 🎬 Kids Animation Pipeline

> **Free, self-hosted automated children's animation generator**
> 
> Generate complete YouTube-ready videos with a single command. All phases automated on GitHub Actions!

## ✨ Features

- 📖 **Original Story Generation** - Ollama LLM creates unique stories
- 🎤 **Text-to-Speech** - eSpeak-ng generates natural narration
- 🎨 **Visual Generation** - Pillow creates cartoon scenes
- 🎬 **Video Composition** - FFmpeg creates professional MP4s
- ⏰ **Daily Automation** - GitHub Actions generates videos every day
- 📺 **YouTube Ready** - H.264 + AAC, proper metadata, optional upload
- 🔓 **Completely Free** - No paid APIs, all open-source

---

## 🚀 Quick Start

### Local Setup (5 minutes)

```bash
# 1. Start services
docker compose up -d

# 2. Generate a video
docker exec kids-channel-worker python -c \
  "import asyncio; from pipeline import generate_story; asyncio.run(generate_story())"

# 3. Check results
ls -lh data/videos/
```

### GitHub Automation (Automatic)

Videos generate **every day at 9 AM UTC** automatically via GitHub Actions!

**Manual trigger:**
1. Go to **Actions** tab
2. Select **"Generate Video (Manual)"**
3. Click **"Run workflow"**
4. Download videos from **Artifacts**

---

## 📦 What You Get

Per video:
- 📝 Story JSON (1-2 KB)
- 🎤 Narration audio (1-1.5 MB)
- 📝 Subtitles (SRT format)
- 🎨 Scene images (4× PNG)
- 🎬 **Final MP4** (500 KB - 1 MB, YouTube-ready)

**Generation time**: 3-6 minutes (CPU) / 30-90 seconds (GPU)

---

## 🏗️ Architecture

```
Story Generation (Ollama LLM)
    ↓
Text-to-Speech (eSpeak-ng)
    ↓
Scene Images (Pillow)
    ↓
Video Composition (FFmpeg)
    ↓
YouTube Upload (Optional OAuth)
    ↓
Complete MP4 Video ✅
```

---

## 📋 System Requirements

- Docker Desktop or Engine
- 8 GB RAM minimum
- 20 GB disk space
- Any OS (Windows, macOS, Linux)

---

## 🎯 All Phases Implemented

| Phase | Feature | Status |
|-------|---------|--------|
| **1** | Story Generation | ✅ |
| **2** | Text-to-Speech | ✅ |
| **3** | Visual Generation | ✅ |
| **3** | Video Composition | ✅ |
| **4** | Background Music | ⚪ Optional |
| **5** | Automation | ✅ GitHub Actions |
| **6** | YouTube Upload | ✅ OAuth Ready |
| **7** | Error Handling | ✅ |

---

## 📚 Documentation

- **[QUICK_START.md](QUICK_START.md)** - 5-minute guide
- **[FINAL_README.md](FINAL_README.md)** - Complete reference
- **[GITHUB_DEPLOYMENT_GUIDE.md](GITHUB_DEPLOYMENT_GUIDE.md)** - GitHub Actions setup
- **[VERIFICATION_CHECKLIST.md](VERIFICATION_CHECKLIST.md)** - 18-point verification
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Comprehensive testing

---

## 🔧 Configuration

Edit `.env`:

```env
# LLM
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2:3b

# Video
VIDEO_WIDTH=1280
VIDEO_HEIGHT=720
VIDEO_FPS=30
VIDEO_BITRATE=2500k

# YouTube (optional)
GENERATE_ONLY=true
```

---

## 🤖 GitHub Actions Workflows

### Daily Generation
- **Trigger**: Every day at 9 AM UTC
- **Runs**: Automatically
- **Output**: Videos in artifacts (30-day retention)

### Manual Generation
- **Trigger**: Click button in GitHub Actions
- **Customizable**: Choose model, number of videos
- **Output**: Videos available for download

### Testing
- **Trigger**: Every push/PR
- **Checks**: Code lint, imports, documentation

---

## 📊 Example Output

```
Story: "Bella's Magical Adventure"
Duration: 22.8 seconds
Format: H.264 + AAC
Resolution: 1280×720 (HD)
Size: 532 KB
Status: ✅ YouTube-ready
```

---

## 🚀 Deployment

### Local Machine
```bash
docker compose up -d
# Run generation command
ls data/videos/  # Check output
```

### GitHub (Automated)
1. Push code to GitHub
2. Enable Actions
3. Videos generate daily automatically
4. Download from artifacts

---

## 📖 How to Use

### Generate Now
```bash
docker exec kids-channel-worker python -c \
  "import asyncio; from pipeline import generate_story; asyncio.run(generate_story())"
```

### Watch Progress
```bash
docker compose logs -f worker
```

### View Results
```bash
ls -lh data/videos/
```

---

## 🔐 Security

- ✅ No credentials in code
- ✅ GitHub Secrets for sensitive data
- ✅ All processing local (nothing leaves machine)
- ✅ Open-source (inspect any file)

---

## 💰 Cost

- **Local**: ~$0 (your hardware)
- **GitHub Actions**: FREE (2,000 min/month included)
- **APIs**: FREE (no paid services required)

---

## 🆘 Troubleshooting

**Can't start services?**
```bash
docker compose down -v
docker compose up -d
```

**Generation hangs?**
Normal on CPU (1-5 min). Check: `docker compose logs ollama`

**Out of storage?**
GitHub Actions stores artifacts 30 days. Delete old runs in Actions tab.

See [TESTING_GUIDE.md](TESTING_GUIDE.md) for more.

---

## 📝 License

MIT - Feel free to use, modify, extend!

---

## ✨ What's Next?

- [ ] Generate your first video
- [ ] Set up GitHub Actions
- [ ] Configure YouTube upload (optional)
- [ ] Deploy n8n for advanced scheduling
- [ ] Explore advanced visuals (Phase 8)

---

## 🤝 Contributing

Found a bug? Have ideas? Feel free to:
1. Open an issue
2. Submit a pull request
3. Improve documentation

---

## 📞 Support

For help:
1. Check [QUICK_START.md](QUICK_START.md)
2. See [TESTING_GUIDE.md](TESTING_GUIDE.md)
3. Review [FINAL_README.md](FINAL_README.md)

---

## 🎬 Ready?

```bash
docker compose up -d
docker exec kids-channel-worker python -c \
  "import asyncio; from pipeline import generate_story; asyncio.run(generate_story())"
```

Check `data/videos/` for your first video! 🚀

---

**Status**: ✅ Production Ready | 🎯 All Phases Complete | 🤖 Fully Automated
