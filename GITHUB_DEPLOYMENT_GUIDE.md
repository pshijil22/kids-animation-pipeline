# 🚀 GitHub Deployment Guide

Your Kids Animation Pipeline is now automated on GitHub!

---

## What You Get

### ✅ GitHub Actions Workflows

1. **test.yml** - Runs on every push/PR
   - Lints code
   - Tests imports
   - Verifies Docker setup
   - Checks documentation

2. **daily-generate.yml** - Runs every day at 9 AM UTC
   - Automatically generates a video
   - Uploads artifacts
   - Runs 24/7

3. **generate-manual.yml** - Manual trigger
   - Click button to generate 1-5 videos
   - Choose model to use
   - Downloads videos as artifacts

---

## Setup (5 Steps)

### Step 1: Create GitHub Repository

Go to https://github.com/new

- Name: `kids-animation-pipeline`
- Description: `Free, self-hosted automated children's animation generator`
- Visibility: Public (recommended for portfolio) or Private
- Click **Create repository**

### Step 2: Clone Locally

```bash
git clone https://github.com/YOUR-USERNAME/kids-animation-pipeline.git
cd kids-animation-pipeline
```

### Step 3: Copy All Files

Copy all files from your local project:

```bash
# From your current project directory
cp -r worker/ /path/to/kids-animation-pipeline/
cp docker-compose.yml /path/to/kids-animation-pipeline/
cp .env.example /path/to/kids-animation-pipeline/
cp *.md /path/to/kids-animation-pipeline/
cp -r prompts/ /path/to/kids-animation-pipeline/
```

Or manually:
- Copy all `.py` files from `worker/` folder
- Copy `docker-compose.yml`
- Copy `.env.example`
- Copy all documentation `.md` files
- Copy `prompts/` folder

### Step 4: Push to GitHub

```bash
cd /path/to/kids-animation-pipeline

# Create .gitignore if needed
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
venv/
env/
.DS_Store
.vscode/
.idea/
EOF

# Commit and push
git add .
git commit -m "Initial commit: Kids Animation Pipeline - Phases 1-7 complete"
git branch -M main
git push -u origin main
```

### Step 5: Enable GitHub Actions

In your GitHub repo:
- Go to **Actions** tab
- Click **"I understand my workflows, go ahead and enable them"**
- Done! ✅

---

## Using GitHub Automation

### Daily Videos (Automatic)

Videos generate **every day at 9 AM UTC** automatically.

To change time, edit `.github/workflows/daily-generate.yml`:

```yaml
schedule:
  - cron: '0 9 * * *'  # 9 AM UTC every day
```

[Cron help](https://crontab.guru/)

### Manual Generation

1. Go to **Actions** tab
2. Select **"Generate Video (Manual)"**
3. Click **"Run workflow"**
4. Enter:
   - **count**: 1-5 videos
   - **model**: llama3.2:3b or tinyllama
5. Click **Run workflow**
6. Wait 5-10 minutes
7. Download videos from **Artifacts**

### View Results

1. Go to **Actions** tab
2. Click any workflow run
3. Scroll down to **Artifacts**
4. Download `generated-video.zip`

---

## GitHub Actions Features

### ✅ What Runs

- **On Every Push**: Tests and validation
- **Every Day at 9 AM**: Generates a video
- **On Demand**: Generate 1-5 videos manually

### ✅ Artifacts Saved

- Generated MP4 videos (30 days)
- Story JSON files (30 days)
- Audio WAV + SRT files (30 days)
- Scene PNG images (30 days)

### ✅ Notifications

- ✉️ Email notifications (GitHub default)
- Optional: Slack/Discord webhooks

### ✅ Cost

**FREE!** GitHub Actions includes:
- 2,000 minutes/month free on public repos
- Unlimited on private repos (if you pay for GitHub Pro)

---

## Customization

### Change Daily Schedule

Edit `.github/workflows/daily-generate.yml`:

```yaml
schedule:
  - cron: '0 9 * * *'  # Change this line
```

Examples:
- `0 9 * * *` = 9 AM UTC daily
- `0 9 * * 1-5` = 9 AM UTC Monday-Friday
- `0 9 * * 0` = 9 AM UTC Sundays only
- `0 */6 * * *` = Every 6 hours

### Change LLM Model

Edit `.github/workflows/daily-generate.yml`:

```yaml
export OLLAMA_MODEL=llama3.2:3b  # Change this
```

Options:
- `llama3.2:3b` (default, fast)
- `mistral` (good quality)
- `neural-chat` (good for chat)
- `tinyllama` (very fast, lower quality)

### Add YouTube Upload

In GitHub repo settings:
1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add new secret `YOUTUBE_CLIENT_ID`
3. Add new secret `YOUTUBE_CLIENT_SECRET`
4. Edit `.github/workflows/daily-generate.yml`:

```yaml
env:
  GENERATE_ONLY: 'false'
  YOUTUBE_CLIENT_ID: ${{ secrets.YOUTUBE_CLIENT_ID }}
  YOUTUBE_CLIENT_SECRET: ${{ secrets.YOUTUBE_CLIENT_SECRET }}
```

---

## Monitoring

### Check Workflow Status

1. Go to **Actions** tab
2. See green ✅ (success) or red ❌ (failed)
3. Click any run to see logs
4. All logs available for debugging

### View Artifacts

1. **Actions** tab
2. Click workflow run
3. Scroll to **Artifacts**
4. Download zip files

### Set Up Notifications

1. Go to **Settings**
2. **Notifications** → Configure
3. Get emailed on failures

---

## Cost Breakdown

### GitHub Actions Usage

**For 1 video per day:**
- ~10 minutes per generation
- ~300 minutes per month
- **Cost: FREE** (within 2,000 min/month limit)

**For 3 videos per day:**
- ~900 minutes per month
- **Cost: FREE**

**For 10 videos per day:**
- ~3,000 minutes per month
- **Cost: ~$0.25/month** (excess paid at $0.25/100 min)

### Storage

- Artifacts keep for 30 days
- Videos deleted after 30 days (or manually)
- **Cost: FREE** (up to limits)

---

## Folder Structure on GitHub

```
kids-animation-pipeline/
├── .github/
│   └── workflows/
│       ├── test.yml                    ← Runs on push
│       ├── daily-generate.yml          ← Daily 9 AM UTC
│       └── generate-manual.yml         ← Manual trigger
│
├── worker/
│   ├── pipeline.py
│   ├── story.py
│   ├── tts.py
│   ├── scenes.py
│   ├── video.py
│   ├── youtube.py
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── prompts/
│   └── story.txt
│
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
├── QUICK_START.md
├── FINAL_README.md
└── ... (documentation files)
```

---

## Example: Complete Setup

```bash
# 1. Create repo on GitHub (https://github.com/new)
# 2. Clone it
git clone https://github.com/YOUR-USERNAME/kids-animation-pipeline.git
cd kids-animation-pipeline

# 3. Copy project files
cp /path/to/original/worker/* worker/
cp /path/to/original/*.md .
cp /path/to/original/*.yml .

# 4. Create .gitignore (see above)

# 5. Commit and push
git add .
git commit -m "Initial commit"
git push -u origin main

# 6. Enable Actions (in GitHub UI)

# ✅ DONE! Automated videos generate every day!
```

---

## 📊 What Happens Next

**Day 1 (Setup)**
- Workflows enabled
- Tests run on your first push ✅

**Every Day (9 AM UTC)**
- Video generated automatically
- Uploaded as artifact (30-day retention)

**When You Need Videos**
- Click **"Run workflow"** in Actions tab
- Videos ready in 10 minutes
- Download as .zip

---

## 🆘 Troubleshooting

### Workflow Doesn't Run

1. Check **Actions** tab is enabled
2. Check `.github/workflows/` files exist
3. Check branch is `main` (default)
4. Try pushing again: `git push`

### Daily Workflow Doesn't Run at Scheduled Time

- GitHub Actions are not guaranteed at exact time
- May delay 15-60 minutes (GitHub's queues)
- Check back later or trigger manually

### Out of Storage

GitHub Actions has limits:
- Public repos: Unlimited
- Private repos: 500 MB (GitHub Pro has more)

Solution: Delete old artifacts or use local machine

### Model Download Fails

The Ollama model (~2GB) downloads during first run:
- Takes 5-10 minutes
- Caches for future runs
- If fails, try manual trigger again

---

## 🎓 Learning Resources

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Cron Schedule Helper](https://crontab.guru/)
- [GitHub Secrets Guide](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

---

## ✅ Next Steps

1. ✅ Create GitHub repo
2. ✅ Push code
3. ✅ Enable Actions
4. ✅ Videos generate automatically!

---

## 🎬 You're All Set!

Your pipeline is now:
- ✅ On GitHub
- ✅ Automated daily
- ✅ Manually triggerable
- ✅ Fully monitored

**Status: LIVE ON GITHUB** 🚀

Videos will generate every day automatically!

Check your **Actions** tab to see them run. ✨
