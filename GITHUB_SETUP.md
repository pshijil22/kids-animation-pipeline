# GitHub Setup Instructions

When you're ready to push this project to GitHub, follow these steps.

## One-Time Setup

### 1. Create a GitHub Repository

Go to https://github.com/new

- **Repository name**: `kids-channel`
- **Description**: "Free, self-hosted automated YouTube children's animation pipeline"
- **Visibility**: `Public` (so others can learn from it)
- **Initialize**: Check "Add a README" (optional, you already have one)
- **License**: MIT (recommended for educational projects)

Click "Create repository"

### 2. Clone Locally (or add remote if you already have the folder)

If you're starting fresh:
```bash
git clone https://github.com/<YOUR_USERNAME>/kids-channel.git
cd kids-channel
# Then copy all the files from this project into the folder
```

If you already have the folder with all files:
```bash
cd kids-channel
git init
git remote add origin https://github.com/<YOUR_USERNAME>/kids-channel.git
```

### 3. First Commit

```bash
git add .
git commit -m "Phase 1: Story generation pipeline with Ollama + Docker"
git branch -M main
git push -u origin main
```

---

## Ongoing Commits

### After Each Phase

**Phase 2 (TTS):**
```bash
git add .
git commit -m "Phase 2: Add text-to-speech with eSpeak-ng"
git push
```

**Phase 3 (Video):**
```bash
git add .
git commit -m "Phase 3: Add visual generation and FFmpeg video creation"
git push
```

And so on...

---

## What Gets Committed

✅ **COMMIT** (to GitHub):
- `*.py` files (code)
- `*.md` files (documentation)
- `docker-compose.yml` (config)
- `.env.example` (template, no secrets)
- `.gitignore` (what NOT to commit)
- `Dockerfile` (container definition)
- `requirements.txt` (dependencies)
- `prompts/` (LLM prompts)
- `ROADMAP.md`, `CHECKLIST.md` (guides)

❌ **DO NOT COMMIT** (git will ignore automatically):
- `.env` (your local config)
- `credentials/` (OAuth tokens)
- `data/` (generated files)
- `__pycache__/` (Python cache)
- `.venv/`, `venv/` (virtual environments)
- `node_modules/` (npm packages)
- `*.log` (log files)
- `.DS_Store` (macOS)

The `.gitignore` file already handles all of this.

---

## Verify Before Pushing

```bash
# Check what will be committed
git status

# Should show:
# - Untracked: .env, credentials/, data/ (these are ignored)
# - Modified/New: *.py, *.md, *.yml files

# Preview commits
git diff --cached | head -100

# If all looks good:
git push
```

---

## GitHub Best Practices

### Commit Messages

Use clear, specific messages:

**Good:**
- `Phase 2: Add text-to-speech with eSpeak-ng`
- `Fix: Ollama retry logic with exponential backoff`
- `Docs: Add Windows quickstart guide`

**Bad:**
- `update`
- `fixes`
- `stuff`

### Branches (Optional)

For bigger changes, use branches:

```bash
git checkout -b feature/phase2-tts
# ... make changes, test ...
git commit -m "Phase 2: Add TTS"
git push origin feature/phase2-tts
# Then create PR on GitHub
```

### README for Others

Your `README.md` is already set up for others to clone and run. They'll see:

1. What the project does
2. Quick start (links to SETUP_GUIDE)
3. Project structure
4. Next phases

People can fork it and contribute!

---

## GitHub Features to Set Up (Optional)

### Enable GitHub Pages

Go to **Settings** → **Pages**
- Source: `main` branch
- Folder: `/root`

Your documentation will be viewable at: `https://<username>.github.io/kids-channel/`

### Add Topics

Go to **About** (top right) → **Topics**

Add: `ai`, `youtube`, `docker`, `automation`, `children`, `storytelling`

This helps others find your project.

### Star/Watch

⭐ If you want to bookmark the repo for yourself, star it

---

## Sharing the Project

Once it's on GitHub, you can:

1. **Share the URL**
   ```
   https://github.com/<USERNAME>/kids-channel
   ```

2. **Allow others to fork and contribute**
   - They can suggest improvements via pull requests

3. **Use as a portfolio project**
   - Employers see you can build full-stack systems
   - Shows Docker, Python, AI, automation skills

4. **Discuss on Reddit, HackerNews, etc.**
   - "I built a free AI video pipeline for kids' animation"
   - People often want to contribute or learn

---

## Future: CI/CD (Later Phases)

When you're ready (Phase 6+), you can add:

### GitHub Actions (Free)

Automatic testing when you push:

```yaml
# .github/workflows/test.yml
name: Test
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: docker/setup-buildx-action@v2
      - run: docker compose build worker
      - run: docker compose up -d
      - run: docker compose exec worker python -m pytest
```

This would automatically test your code before committing.

For now, skip this—Phase 1 doesn't have tests yet. We'll add it later.

---

## Quick Reference: Git Commands

```bash
# Initial setup (once)
git init
git remote add origin https://github.com/<USERNAME>/kids-channel.git

# Normal workflow
git status                          # See what changed
git add .                          # Stage all changes
git commit -m "Your message"       # Create commit
git push                           # Push to GitHub

# Later, if you pull on another computer
git clone https://github.com/<USERNAME>/kids-channel.git
cd kids-channel
cp .env.example .env
docker compose up -d
```

---

## You're Set!

When you're ready:

1. Create GitHub repo
2. `git add .` and `git commit`
3. `git push`
4. Your project is live for the world to see

---

**Phase 1 is complete and ready to share. Good luck!**
