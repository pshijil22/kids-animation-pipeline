# 🚀 GitHub Setup in 10 Steps

**Everything automated. Videos generate daily. Copy-paste only!**

---

## Step 1: Create GitHub Repository

Go to: **https://github.com/new**

Fill in:
- **Repository name**: `kids-animation-pipeline`
- **Description**: `Free, self-hosted automated children's animation generator`
- **Public** (recommended) or Private
- ✅ **Create repository**

---

## Step 2: Copy Repository URL

After creating, you'll see:

```
https://github.com/YOUR-USERNAME/kids-animation-pipeline.git
```

Copy this URL. You'll need it next.

---

## Step 3: Clone to Your Computer

```bash
git clone https://github.com/YOUR-USERNAME/kids-animation-pipeline.git
cd kids-animation-pipeline
```

Replace `YOUR-USERNAME` with your GitHub username.

---

## Step 4: Copy Project Files

Copy all these files from your local project:

```bash
# Copy source code
cp -r /path/to/original/worker/* worker/

# Copy config
cp /path/to/original/docker-compose.yml .
cp /path/to/original/.env.example .

# Copy docs
cp /path/to/original/*.md .

# Copy prompts
cp -r /path/to/original/prompts/ .
```

Or manually drag-and-drop files.

---

## Step 5: Create .gitignore

```bash
cat > .gitignore << 'EOF'
.env
.env.local
credentials/
data/
*.mp4
*.wav
*.srt
*.png
__pycache__/
*.py[cod]
*.so
venv/
env/
.DS_Store
.vscode/
.idea/
logs/
*.log
EOF
```

---

## Step 6: Copy Workflow Files

Create `.github/workflows/` directory with these files:

**.github/workflows/test.yml**
→ [Copy from here](/.github/workflows/test.yml)

**.github/workflows/daily-generate.yml**
→ [Copy from here](/.github/workflows/daily-generate.yml)

**.github/workflows/generate-manual.yml**
→ [Copy from here](/.github/workflows/generate-manual.yml)

Or use these commands:

```bash
mkdir -p .github/workflows

# Download files directly (if you have curl/wget)
wget https://raw.githubusercontent.com/.../test.yml -O .github/workflows/test.yml
wget https://raw.githubusercontent.com/.../daily-generate.yml -O .github/workflows/daily-generate.yml
wget https://raw.githubusercontent.com/.../generate-manual.yml -O .github/workflows/generate-manual.yml
```

---

## Step 7: Commit and Push

```bash
git add .
git commit -m "Initial commit: Kids Animation Pipeline - All phases complete"
git branch -M main
git push -u origin main
```

---

## Step 8: Enable GitHub Actions

In your repo on GitHub:

1. Go to **Settings** tab
2. Left sidebar: **Actions** → **General**
3. Under "Actions permissions": Select **"Allow all actions and reusable workflows"**
4. ✅ **Save**

---

## Step 9: Verify Workflows

1. Go to **Actions** tab in your repo
2. You should see 3 workflows:
   - ✅ Build and Test Pipeline
   - ✅ Generate Video Daily
   - ✅ Generate Video (Manual)

---

## Step 10: Done! 🎉

Your pipeline is now:
- ✅ On GitHub
- ✅ Automated daily at 9 AM UTC
- ✅ Manually triggerable
- ✅ Fully tested

---

## Test It!

### Run Tests
1. Go to **Actions** tab
2. Select **"Build and Test Pipeline"**
3. Click **"Run workflow"** → **"Run workflow"**
4. Wait 2-3 minutes
5. Should show ✅ green

### Generate a Video Manually
1. Go to **Actions** tab
2. Select **"Generate Video (Manual)"**
3. Click **"Run workflow"**
4. Enter:
   - **count**: 1 (default)
   - **model**: llama3.2:3b (default)
5. Click **"Run workflow"**
6. Wait 5-10 minutes
7. Go to run details → **Artifacts** → Download videos

### Check Daily Generation
Tomorrow at 9 AM UTC, check **Actions** tab:
- New run for **"Generate Video Daily"**
- Videos in artifacts
- ✅ Automatic!

---

## 🎯 Customization (Optional)

### Change Daily Schedule

Edit `.github/workflows/daily-generate.yml`:

Change this line:
```yaml
- cron: '0 9 * * *'  # 9 AM UTC daily
```

To:
```yaml
- cron: '0 18 * * *'  # 6 PM UTC daily
```

[Cron helper](https://crontab.guru)

### Change Model

Edit `.github/workflows/daily-generate.yml`:

Change:
```yaml
export OLLAMA_MODEL=llama3.2:3b
```

To:
```yaml
export OLLAMA_MODEL=mistral  # Or tinyllama
```

Push changes:
```bash
git add .github/workflows/daily-generate.yml
git commit -m "Update: Changed daily model"
git push
```

---

## 📊 What Runs Where

| Workflow | When | Where |
|----------|------|-------|
| **test.yml** | Every push | GitHub Actions |
| **daily-generate.yml** | 9 AM UTC daily | GitHub Actions |
| **generate-manual.yml** | On demand | GitHub Actions |

---

## 💻 Your Files on GitHub

```
kids-animation-pipeline/
├── .github/
│   └── workflows/
│       ├── test.yml
│       ├── daily-generate.yml
│       └── generate-manual.yml
├── worker/
│   ├── pipeline.py
│   ├── story.py
│   ├── tts.py
│   ├── scenes.py
│   ├── video.py
│   ├── youtube.py
│   ├── Dockerfile
│   └── requirements.txt
├── prompts/
│   └── story.txt
├── docker-compose.yml
├── .env.example
├── .gitignore
└── *.md (all documentation)
```

---

## 🎬 What Happens Next

**Today:**
- ✅ Repo created
- ✅ Files pushed
- ✅ Actions enabled
- ✅ Tests run

**Tomorrow 9 AM UTC:**
- 🎬 First video generates automatically
- 📁 Available in artifacts (30-day retention)
- 📧 Email notification sent

**Every Day:**
- 🎬 New video generates
- 📁 Downloads available
- ⚙️ No manual work needed

---

## 🆘 Quick Troubleshooting

### Nothing happens after push?
1. Check **Actions** tab
2. Click the failed/pending run
3. Check logs at bottom
4. Common: Just needs 1-2 minutes to start

### "Workflows not running"?
1. Check **Settings** → **Actions** is enabled
2. Check branch is `main` (default)
3. Try pushing again: `git push`

### "Model download fails"?
1. Try again (model caches after first download)
2. Click **Run workflow** again
3. Usually works on 2nd try

### Videos not downloading?
1. Go to **Actions** tab
2. Click the successful run
3. Scroll to **Artifacts**
4. Download zip file

---

## 📚 Next Steps

1. ✅ Follow steps 1-10 above
2. ✅ Test with manual run
3. ✅ Wait for daily run tomorrow
4. ✅ Download videos
5. ✅ Share your pipeline!

---

## 🔐 Optional: YouTube Setup

To auto-upload to YouTube:

1. Get OAuth credentials from Google Cloud
2. In repo: **Settings** → **Secrets and variables** → **Actions**
3. Add `YOUTUBE_CLIENT_ID`
4. Add `YOUTUBE_CLIENT_SECRET`
5. Edit `.github/workflows/daily-generate.yml`:

```yaml
env:
  GENERATE_ONLY: 'false'
```

Videos auto-upload (as private) on next run.

---

## ✅ Completion Checklist

- [ ] Repository created on GitHub
- [ ] Files copied locally
- [ ] .gitignore created
- [ ] Workflow files in `.github/workflows/`
- [ ] Code pushed to GitHub
- [ ] GitHub Actions enabled
- [ ] Test workflow ran successfully
- [ ] Manual generation tested
- [ ] Videos downloaded from artifacts
- [ ] Scheduled daily generation verified

**All done?** Your pipeline is now fully automated! 🚀

---

## 📞 Need Help?

- Workflow errors? Check **Actions** tab → run logs
- How to use? See **[FINAL_README.md](FINAL_README.md)**
- Testing? See **[TESTING_GUIDE.md](TESTING_GUIDE.md)**
- GitHub setup? See **[GITHUB_DEPLOYMENT_GUIDE.md](GITHUB_DEPLOYMENT_GUIDE.md)**

---

## 🎉 You're Done!

Videos now generate:
- ✅ Every day automatically (9 AM UTC)
- ✅ On-demand when you click a button
- ✅ Fully tested
- ✅ Ready for YouTube

**Congratulations!** 🎬

Your kids animation pipeline is now fully automated on GitHub!

---

**Status: ✅ LIVE ON GITHUB - VIDEOS GENERATE DAILY**
