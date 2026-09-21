# 📁 FILE STORAGE CONFIGURATION - CHANGED

**Storage Location Updated:** `C:\Users\pshij\Downloads\default`

---

## What Changed

### Old Configuration
```yaml
volumes:
  - ./data:/data  # Relative path to project folder
```

### New Configuration
```yaml
volumes:
  - C:/Users/pshij/Downloads/default:/data  # Your Downloads folder
```

---

## What Gets Stored There

All generated files will now be saved to: `C:\Users\pshij\Downloads\default\`

This includes:
- 📹 **videos/** - Generated MP4 files
- 📖 **stories/** - Story JSON files
- 🎤 **audio/** - Narration WAV and subtitles
- 🖼️ **scenes/** - Scene PNG images
- 📊 **logs/** - Execution logs

---

## Directory Structure

After running, you'll see:

```
C:\Users\pshij\Downloads\default\
├── videos/
│   ├── 20260919_234730.mp4
│   └── ... (more videos)
├── stories/
│   ├── 20260919_234730_story.json
│   └── ...
├── audio/
│   ├── 20260919_234730_narration.wav
│   ├── 20260919_234730_subtitles.srt
│   └── ...
├── scenes/
│   ├── 20260919_234730_scene_01.png
│   └── ...
└── logs/
    └── pipeline.log
```

---

## Files Updated

✅ **docker-compose.yml**
- Changed data volume path
- Now points to Downloads folder

✅ **.env.example**
- Added `DATA_DIR` variable
- Shows new storage location

---

## How to Apply

### Option 1: Just Use It (Automatic)

When you restart Docker:
```bash
docker compose down
docker compose up -d
```

The container will automatically use the new path.

### Option 2: Create the Folder First (Recommended)

Before running:
```bash
# Create the folder if it doesn't exist
mkdir C:\Users\pshij\Downloads\default
```

Then restart:
```bash
docker compose restart
```

---

## Verification

### Check Volume Mounting

```bash
docker inspect kids-channel-worker | grep -A 5 Mounts
```

Should show:
```
"Mounts": [
    {
        "Type": "bind",
        "Source": "C:\\Users\\pshij\\Downloads\\default",
        "Destination": "/data"
    }
]
```

### Generate a Test Video

```bash
docker exec kids-channel-worker python -c "import asyncio; from pipeline import generate_story; asyncio.run(generate_story())"
```

Then check:
```bash
ls C:\Users\pshij\Downloads\default\videos\
```

Should show your generated MP4 file.

---

## Backup Current Data (If Needed)

If you had data in the old `./data` folder:

```bash
# Backup old data
copy /Y .\data\* C:\Users\pshij\Downloads\default\
```

---

## Next Steps

1. ✅ Files updated (docker-compose.yml + .env.example)
2. ✅ Push to GitHub:
   ```bash
   git add docker-compose.yml .env.example
   git commit -m "Change: Update file storage location to Downloads folder"
   git push origin main
   ```
3. ✅ Restart Docker:
   ```bash
   docker compose down
   docker compose up -d
   ```
4. ✅ Test by generating a video
5. ✅ Verify files in Downloads folder

---

## Benefits

✅ Files stored in a familiar location (Downloads)
✅ Easy to access generated videos
✅ Backup-friendly (outside project folder)
✅ No project bloat
✅ Can clear data independently

---

**Storage location changed! Generated files will now save to your Downloads folder.** 📁
