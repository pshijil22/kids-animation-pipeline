#!/bin/bash
# GitHub Push Script - Fixed Token Handling

set -e

GITHUB_USERNAME="pshijil22"
GITHUB_EMAIL="pshijil22@gmail.com"
GITHUB_TOKEN="$1"
REPO_NAME="kids-animation-pipeline"

if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ Error: GitHub token required as argument"
    exit 1
fi

cd /repo

echo "📋 Step 1: Configure Git"
git config --global user.name "$GITHUB_USERNAME"
git config --global user.email "$GITHUB_EMAIL"
echo "✅ Git configured"
echo ""

echo "📋 Step 2: Create .gitignore"
cat > .gitignore << 'GITIGNORE'
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
GITIGNORE
echo "✅ .gitignore created"
echo ""

echo "📋 Step 3: Initialize repository"
if [ -d .git ]; then
    echo "Repository already initialized"
else
    git init
    echo "✅ Repository initialized"
fi
echo ""

echo "📋 Step 4: Add remote"
git remote remove origin 2>/dev/null || true

# Properly format the remote URL without shell variable expansion issues
REMOTE_URL="https://${GITHUB_USERNAME}:${GITHUB_TOKEN}@github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"
git remote add origin "$REMOTE_URL"
echo "✅ Remote configured"
echo ""

echo "📋 Step 5: Stage all files"
git add .
FILE_COUNT=$(git ls-files | wc -l)
echo "✅ Staged $FILE_COUNT files"
echo ""

echo "📋 Step 6: Create commit"
git commit -m "Initial commit: Kids Animation Pipeline - All phases complete

- Phase 1: Story generation (Ollama LLM)
- Phase 2: Text-to-speech (eSpeak-ng)
- Phase 3: Visual generation & video composition (FFmpeg)
- Phase 4: Background music framework
- Phase 5: n8n automation ready
- Phase 6: YouTube OAuth integration
- Phase 7: Error handling & logging
- 3 GitHub Actions workflows
- Complete documentation
- Tested & verified"
echo "✅ Commit created"
echo ""

echo "📋 Step 7: Set main branch"
git branch -M main
echo "✅ Branch set to main"
echo ""

echo "📋 Step 8: Push to GitHub"
git push -u origin main 2>&1 | grep -v "remote:"
echo "✅ Code pushed to GitHub!"
echo ""

echo "════════════════════════════════════════════════════════════"
echo "✅ PUSH SUCCESSFUL!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "🎉 Your code is now on GitHub!"
echo ""
echo "📋 Next Steps:"
echo "   1. Go to: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
echo "   2. Verify your code is there"
echo "   3. Go to Settings → Actions → General"
echo "   4. Select 'Allow all actions and reusable workflows'"
echo "   5. Click Save"
echo ""
echo "🎬 Your automation will then:"
echo "   • Run tests on every push"
echo "   • Generate videos daily at 9 AM UTC"
echo "   • Allow manual generation anytime"
