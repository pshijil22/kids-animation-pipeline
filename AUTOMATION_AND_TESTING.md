# 🤖 GITHUB AUTOMATION & TESTING GUIDE

**Your code is on GitHub! Now let's automate and test it.**

---

## ✅ VERIFICATION STEPS (First)

### Step 1: Verify Your Repository

Go to: **https://github.com/pshijil22/kids-animation-pipeline**

You should see:
- ✅ All your files
- ✅ Commit history
- ✅ README.md displayed

**Confirmed?** (Yes/No)

---

### Step 2: Check Workflows Uploaded

1. Go to **Actions** tab
2. You should see 3 workflows:
   - ✅ Build and Test Pipeline
   - ✅ Generate Video Daily
   - ✅ Generate Video (Manual)

**All 3 visible?** (Yes/No)

---

### Step 3: Enable GitHub Actions

1. Click **Settings** (top right)
2. Left sidebar: **Actions** → **General**
3. Under "Actions permissions": Select **"Allow all actions and reusable workflows"**
4. Click **Save**

**Enabled?** (Yes/No)

---

## 🤖 AUTOMATION SETUP

### Automation 1: Continuous Integration (On Every Push)

**What happens:**
- Every time you push code, tests run automatically
- Validates code, checks imports, verifies Docker setup
- Shows ✅ green or ❌ red status

**Test it:**
1. Go to **Actions** tab
2. Click **"Build and Test Pipeline"**
3. You should see workflow runs
4. Click latest run to see details

**Check status:**
- ✅ Green = All tests passed
- ❌ Red = Something failed (see logs)

---

### Automation 2: Daily Video Generation

**What happens:**
- Every day at **9 AM UTC**, a video generates automatically
- Saved to artifacts for 30 days
- Email notification sent

**To verify it's scheduled:**
1. Go to **Actions** tab
2. Click **"Generate Video Daily"**
3. Check the workflow file details

**To manually test:**
1. Go to **Actions** tab
2. Click **"Generate Video Daily"**
3. Click **"Run workflow"** button (top right)
4. Select branch: **main**
5. Click **"Run workflow"**

Wait 10-15 minutes, then check for artifacts.

---

### Automation 3: Manual On-Demand Generation

**What happens:**
- Click a button to generate videos anytime
- Specify how many (1-5) and which model
- Videos ready in 5-10 minutes

**To test:**
1. Go to **Actions** tab
2. Click **"Generate Video (Manual)"**
3. Click **"Run workflow"** button
4. Fill in:
   - **count**: `1` (generate 1 video)
   - **model**: `llama3.2:3b`
5. Click **"Run workflow"**

Wait 5-10 minutes for completion.

---

## 🧪 TESTING STEPS

### Test 1: Run CI/CD Pipeline

**Purpose:** Verify code quality and dependencies

**Steps:**
1. Go to **Actions** tab
2. Click **"Build and Test Pipeline"**
3. Click **"Run workflow"** button
4. Wait 3-5 minutes
5. Should show ✅ green checkmark

**Expected output:**
- ✅ Code linted
- ✅ Imports tested
- ✅ Docker files verified
- ✅ Documentation checked

**If RED (failed):**
- Click the run
- Scroll down to see error logs
- Fix code locally and push again

---

### Test 2: Generate Single Test Video

**Purpose:** Verify complete pipeline works

**Steps:**
1. Go to **Actions** tab
2. Click **"Generate Video (Manual)"**
3. Click **"Run workflow"**
4. Set:
   - **count**: `1`
   - **model**: `llama3.2:3b`
5. Click **"Run workflow"**

**Wait 5-10 minutes...**

Then:
1. Go back to the completed run
2. Scroll down to **Artifacts**
3. Should see:
   - ✅ `videos-XXXXX.zip`
   - ✅ `stories-XXXXX.zip`
   - ✅ `audio-XXXXX.zip`

**Download and verify:**
- Extract videos zip
- Open MP4 in media player
- Should be playable with audio and subtitles

---

### Test 3: Verify Daily Schedule

**Purpose:** Confirm daily automation is set

**Steps:**
1. Go to **Actions** tab
2. Click **"Generate Video Daily"**
3. View workflow file (`.github/workflows/daily-generate.yml`)
4. Check the `schedule` section shows:
   ```
   - cron: '0 9 * * *'  # 9 AM UTC daily
   ```

**If correct:**
- ✅ Videos will generate tomorrow at 9 AM UTC

**To change time:**
1. Go to `.github/workflows/daily-generate.yml`
2. Edit the cron schedule
3. Commit changes
4. Automation updates automatically

Example:
```
'0 18 * * *'   # 6 PM UTC daily
'0 9 * * 1-5'  # 9 AM UTC Mon-Fri only
```

---

### Test 4: Check Artifacts Storage

**Purpose:** Verify videos are being saved

**Steps:**
1. Go to **Actions** tab
2. Find any completed workflow run
3. Scroll down to **Artifacts**
4. You should see generated files

**Artifacts include:**
- ✅ Generated MP4 videos
- ✅ Story JSON files
- ✅ Audio WAV files
- ✅ Scene PNG images
- ✅ Subtitles SRT files

**Retention:**
- All artifacts kept for 30 days
- Can download anytime
- Automatically deleted after 30 days

---

## 📊 MONITORING AUTOMATION

### Check Status Anytime

1. Go to **Actions** tab
2. See all workflow runs
3. Click any run for details
4. Check logs and artifacts

### Set Up Notifications

**Email notifications (default):**
- GitHub sends email on workflow failure
- Check spam folder if not seeing emails

**Set custom notifications:**
1. Go to **Settings** (top right of GitHub)
2. **Notifications**
3. Configure email preferences
4. Choose when to receive alerts

---

## ⚙️ ADJUSTMENTS & CUSTOMIZATION

### Change Daily Generation Time

**File:** `.github/workflows/daily-generate.yml`

**Find line:**
```yaml
- cron: '0 9 * * *'
```

**Change to:**
```yaml
- cron: '0 18 * * *'  # 6 PM UTC instead
```

**Commit and push** → Automation updates automatically

### Change LLM Model

**File:** `.github/workflows/daily-generate.yml`

**Find line:**
```yaml
export OLLAMA_MODEL=llama3.2:3b
```

**Change to:**
```yaml
export OLLAMA_MODEL=mistral  # or tinyllama
```

**Commit and push** → Uses new model next time

### Increase Video Quality

**File:** `.github/workflows/daily-generate.yml`

**Find line:**
```yaml
VIDEO_BITRATE=2500k
```

**Change to:**
```yaml
VIDEO_BITRATE=4000k  # Higher quality
```

**Commit and push** → Higher bitrate videos

---

## 🎬 EXPECTED RESULTS

### First Time Running CI/CD

**Expected:**
- ✅ Tests pass (green)
- ⏱️ Takes 3-5 minutes
- 📊 Shows all checks passed

### First Manual Video Generation

**Expected:**
- ⏱️ Takes 5-10 minutes
- 📹 Creates MP4 video (~500 KB - 1 MB)
- 📊 Shows 3 artifact zips
- 📊 Video is playable

### First Daily Automatic Run

**Expected:**
- ⏰ Happens at scheduled time (9 AM UTC)
- 📧 Email notification sent
- 📹 Artifacts available in Actions
- 🔄 Repeats every day

---

## 🆘 TROUBLESHOOTING

### Workflows Don't Show Up

**Solution:**
1. Check **Settings** → **Actions** is enabled
2. Check you're on `main` branch
3. Refresh the Actions tab
4. Wait 1-2 minutes for sync

### Test Workflow Fails (Red ❌)

**Solution:**
1. Click the failed run
2. Scroll down to see error logs
3. Common issues:
   - Missing dependencies → Check requirements.txt
   - Import errors → Check Python imports
   - Docker issues → Check Dockerfile syntax
4. Fix and push again

### Manual Generation Times Out

**Solution:**
- Normal on first run (model downloads)
- Takes 5-10 minutes on CPU
- Retry if it fails
- Video should still generate

### No Artifacts Created

**Solution:**
1. Check workflow completed (not still running)
2. Scroll down in run details
3. Artifacts section should be visible
4. If missing, check logs for errors

### Daily Generation Didn't Run

**Solution:**
1. Check scheduled time (9 AM UTC)
2. GitHub queues can delay by 15-60 min
3. Check back later
4. Or manually trigger to test

---

## ✅ COMPLETE AUTOMATION CHECKLIST

After setup:

- [ ] Repository visible on GitHub
- [ ] All files uploaded
- [ ] 3 workflows showing in Actions tab
- [ ] GitHub Actions enabled (Settings)
- [ ] CI/CD test run completed (✅ green)
- [ ] Manual generation tested (artifacts created)
- [ ] Daily schedule verified (9 AM UTC)
- [ ] Email notifications working

**All checked? Automation is live!** 🎉

---

## 🚀 DAILY WORKFLOW

**You don't need to do anything!**

### Automatic:
- ✅ Every day at 9 AM UTC = Video generates
- ✅ Email notification sent
- ✅ Download from artifacts

### Optional (Manual):
- ✅ Click "Run workflow" anytime
- ✅ Generate video on-demand
- ✅ Ready in 5-10 minutes

---

## 📞 SUPPORT

**If something fails:**
1. Check Actions tab for error logs
2. See "Troubleshooting" section above
3. Common fixes:
   - Re-enable Actions
   - Push code changes to trigger CI
   - Manually run workflow to test

---

**Your automation is now live! Everything runs without manual intervention.** 🤖

Videos generate daily at 9 AM UTC automatically!
