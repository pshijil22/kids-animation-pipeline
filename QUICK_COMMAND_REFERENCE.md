# 🎯 QUICK REFERENCE - COPY-PASTE COMMANDS

**Follow these exact commands in order. Replace YOUR-TOKEN with your actual GitHub token.**

---

## STEP 1: Create GitHub Repository
- Go to: https://github.com/new
- Name: `kids-animation-pipeline`
- Visibility: PUBLIC
- Do NOT initialize
- Create

---

## STEP 2: Terminal Commands (Copy-Paste)

### 2a: Navigate to your project folder
```bash
cd /path/to/kids-animation-pipeline
```

### 2b: Initialize Git
```bash
git init
```

### 2c: Configure Git
```bash
git config --global user.name "pshijil22"
git config --global user.email "pshijil22@gmail.com"
```

### 2d: Create .gitignore

**Windows PowerShell:**
```powershell
@'
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
.Python
venv/
ENV/
env/
.venv
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
logs/
*.log
Thumbs.db
'@ | Set-Content -Path .gitignore
```

**Mac/Linux Bash:**
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
.Python
venv/
ENV/
env/
.venv
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
logs/
*.log
Thumbs.db
EOF
```

### 2e: Add Remote (⚠️ REPLACE YOUR-TOKEN WITH ACTUAL TOKEN)
```bash
git remote add origin https://pshijil22:YOUR-TOKEN@github.com/pshijil22/kids-animation-pipeline.git
```

### 2f: Verify Remote
```bash
git remote -v
```

### 2g: Add All Files
```bash
git add .
```

### 2h: Create Commit
```bash
git commit -m "Initial commit: Kids Animation Pipeline - All phases complete"
```

### 2i: Set Main Branch
```bash
git branch -M main
```

### 2j: Push to GitHub
```bash
git push -u origin main
```

---

## STEP 3: Validate on GitHub

### Check 1: Files Uploaded
- Go to: https://github.com/pshijil22/kids-animation-pipeline
- Should see: worker/, .github/, docker-compose.yml, README.md, etc.

### Check 2: Workflows Visible
- Click: **Actions** tab
- Should see 3 workflows:
  - Build and Test Pipeline
  - Generate Video Daily
  - Generate Video (Manual)

### Check 3: Enable Actions
- Click: **Settings**
- Left sidebar: **Actions** → **General**
- Select: **"Allow all actions and reusable workflows"**
- Click: **Save**

### Check 4: Run Test Workflow
- Go to: **Actions** tab
- Click: **"Build and Test Pipeline"**
- Click: **"Run workflow"**
- Wait 3-5 minutes for ✅ green checkmark

### Check 5: Test Manual Generation
- Go to: **Actions** tab
- Click: **"Generate Video (Manual)"**
- Click: **"Run workflow"**
- Set: count=1, model=llama3.2:3b
- Wait 5-10 minutes
- Check: Artifacts (videos-XXXX.zip)

---

## ✅ SUCCESS INDICATORS

You're done when:
- ✅ All files on GitHub
- ✅ 3 workflows visible
- ✅ Test workflow passed (green)
- ✅ Manual generation created artifacts
- ✅ Actions enabled
- ✅ Daily schedule set

---

## 🎬 AFTER PUSH

**Tomorrow 9 AM UTC:**
- First video generates automatically
- Available in GitHub Artifacts
- Email notification sent

**Anytime:**
- Manual: Click "Run workflow" in Actions
- Videos ready in 5-10 minutes

---

## ⚠️ COMMON MISTAKES TO AVOID

❌ Using old/expired token → Use FRESH token
❌ Repository with README pre-initialized → Create EMPTY repo
❌ Pushing from wrong folder → Verify: `ls` shows worker/, prompts/, docker-compose.yml
❌ Forgetting to enable Actions → Must do: Settings → Actions → Allow all
❌ Wrong username in token URL → Must be: `pshijil22`

---

**READY? Start with "Create GitHub Repository" above!**
