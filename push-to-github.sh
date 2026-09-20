#!/bin/bash
# Automated Git Push & GitHub Setup Script
# This script handles everything: init, commit, push, and GitHub Actions setup

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     Kids Animation Pipeline - Automated GitHub Setup          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if all required files exist
check_files() {
    echo "Checking project files..."
    
    required_files=(
        "docker-compose.yml"
        ".env.example"
        "worker/pipeline.py"
        "worker/Dockerfile"
        "worker/requirements.txt"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            echo "❌ Missing: $file"
            exit 1
        fi
    done
    
    echo "✅ All required files found"
}

# Initialize git repository
init_git() {
    echo ""
    echo "Initializing Git repository..."
    
    if [ -d .git ]; then
        echo "⚠️  Git repository already exists, skipping init"
    else
        git init
        echo "✅ Git initialized"
    fi
}

# Create comprehensive .gitignore
create_gitignore() {
    echo ""
    echo "Creating .gitignore..."
    
    cat > .gitignore << 'EOF'
# Environment variables
.env
.env.local
.env.*.local

# Credentials (NEVER COMMIT THESE)
credentials/
*.json
!prompts/

# Data outputs
data/
*.mp4
*.wav
*.srt
*.png

# Docker
.docker/
docker-compose.override.yml

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
venv/
ENV/
env/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Logs
logs/
*.log

# OS
Thumbs.db
.DS_Store
EOF
    
    echo "✅ .gitignore created"
}

# Add all files
add_files() {
    echo ""
    echo "Adding files to Git..."
    
    git add .
    
    # Count files
    file_count=$(git ls-files | wc -l)
    echo "✅ $file_count files staged for commit"
}

# Create initial commit
create_commit() {
    echo ""
    echo "Creating initial commit..."
    
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
    
    echo "✅ Initial commit created"
}

# Configure remote
configure_remote() {
    echo ""
    echo "Configuring remote repository..."
    
    # Check if remote already exists
    if git remote get-url origin &>/dev/null; then
        echo "ℹ️  Remote 'origin' already configured"
        git remote get-url origin
    else
        echo ""
        echo "⚠️  No remote repository configured yet"
        echo ""
        echo "To push to GitHub:"
        echo "1. Create a repository at: https://github.com/new"
        echo "2. Name it: kids-animation-pipeline"
        echo "3. DO NOT initialize with README/gitignore"
        echo "4. Then run:"
        echo ""
        echo "   git remote add origin https://github.com/YOUR-USERNAME/kids-animation-pipeline.git"
        echo "   git branch -M main"
        echo "   git push -u origin main"
        echo ""
        return
    fi
}

# Push to GitHub
push_to_github() {
    echo ""
    read -p "Push to GitHub now? (y/n) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Pushing to GitHub..."
        git branch -M main
        git push -u origin main
        echo "✅ Code pushed to GitHub!"
    else
        echo "⏭️  Skipping push. Run when ready:"
        echo "   git push -u origin main"
    fi
}

# Main execution
main() {
    check_files
    init_git
    create_gitignore
    add_files
    create_commit
    configure_remote
    push_to_github
    
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "✅ GIT SETUP COMPLETE"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo "Next steps:"
    echo "1. Create GitHub repository: https://github.com/new"
    echo "2. Configure remote: git remote add origin <your-repo-url>"
    echo "3. Push code: git push -u origin main"
    echo "4. Enable Actions: Settings → Actions → Allow all"
    echo "5. Workflows run automatically!"
    echo ""
}

main "$@"
