#!/bin/bash
# Automated GitHub Push using Docker
# Run this from your project directory

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     Kids Animation Pipeline - Docker-Based GitHub Push       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Configuration
GITHUB_USERNAME="pshijil22"
GITHUB_EMAIL="pshijil22@gmail.com"
GITHUB_TOKEN="$1"  # Pass token as argument
REPO_NAME="kids-animation-pipeline"
REPO_URL="https://${GITHUB_TOKEN}@github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"

if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ ERROR: GitHub token not provided"
    echo "Usage: ./docker-push.sh YOUR_GITHUB_TOKEN"
    exit 1
fi

echo "📋 Configuration:"
echo "   Username: $GITHUB_USERNAME"
echo "   Email: $GITHUB_EMAIL"
echo "   Repository: $REPO_NAME"
echo ""

# Create .gitignore
echo "Creating .gitignore..."
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
echo "✅ .gitignore created"

# Run git operations in Docker
echo ""
echo "Running Git operations in Docker..."
echo ""

docker run --rm \
  -v "$(pwd):/workspace" \
  -e GITHUB_TOKEN="$GITHUB_TOKEN" \
  alpine/git:latest \
  sh -c "
    cd /workspace
    
    echo '📋 Step 1: Configure Git'
    git config --global user.name '$GITHUB_USERNAME'
    git config --global user.email '$GITHUB_EMAIL'
    echo '✅ Git configured'
    
    echo ''
    echo '📋 Step 2: Initialize repository'
    if [ -d .git ]; then
      echo 'Repository already exists'
    else
      git init
      echo '✅ Repository initialized'
    fi
    
    echo ''
    echo '📋 Step 3: Add remote'
    git remote remove origin 2>/dev/null || true
    git remote add origin '$REPO_URL'
    echo '✅ Remote configured'
    
    echo ''
    echo '📋 Step 4: Stage files'
    git add .
    FILE_COUNT=\$(git ls-files | wc -l)
    echo \"✅ Staged \$FILE_COUNT files\"
    
    echo ''
    echo '📋 Step 5: Create commit'
    git commit -m 'Initial commit: Kids Animation Pipeline - All phases complete

- Phase 1: Story generation (Ollama LLM)
- Phase 2: Text-to-speech (eSpeak-ng)
- Phase 3: Visual generation & video composition (FFmpeg)
- Phase 4: Background music framework
- Phase 5: n8n automation ready
- Phase 6: YouTube OAuth integration
- Phase 7: Error handling & logging
- 3 GitHub Actions workflows
- Complete documentation
- Tested & verified'
    echo '✅ Commit created'
    
    echo ''
    echo '📋 Step 6: Set main branch'
    git branch -M main
    echo '✅ Branch set to main'
    
    echo ''
    echo '📋 Step 7: Push to GitHub'
    git push -u origin main
    echo '✅ Code pushed to GitHub'
    
    echo ''
    echo '════════════════════════════════════════════════════════'
    echo '✅ PUSH SUCCESSFUL!'
    echo '════════════════════════════════════════════════════════'
  "

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "🎉 SUCCESS! Your code is now on GitHub"
    echo ""
    echo "📋 Next Steps:"
    echo "   1. Go to: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
    echo "   2. Verify your code is there"
    echo "   3. Go to Settings → Actions → General"
    echo "   4. Select 'Allow all actions and reusable workflows'"
    echo "   5. Click Save"
    echo ""
    echo "🎬 Your automation is now live!"
    echo "   • Tests run on every push"
    echo "   • Videos generate daily at 9 AM UTC"
    echo "   • Manual trigger available anytime"
else
    echo ""
    echo "❌ PUSH FAILED (Exit code: $EXIT_CODE)"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   1. Verify GitHub token is valid"
    echo "   2. Verify repository exists on GitHub: https://github.com/new"
    echo "   3. Check internet connection"
    echo "   4. Try running again"
fi

exit $EXIT_CODE
