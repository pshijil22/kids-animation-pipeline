# Automated Git Push & GitHub Setup Script (PowerShell)
# This script handles everything: init, commit, push, and GitHub Actions setup

param(
    [string]$GitHubUsername,
    [string]$RepositoryName = "kids-animation-pipeline"
)

Write-Host "`n╔════════════════════════════════════════════════════════════════╗"
Write-Host "║     Kids Animation Pipeline - Automated GitHub Setup          ║"
Write-Host "╚════════════════════════════════════════════════════════════════╝`n"

# Check if all required files exist
function Check-Files {
    Write-Host "Checking project files..."
    
    $requiredFiles = @(
        "docker-compose.yml",
        ".env.example",
        "worker/pipeline.py",
        "worker/Dockerfile",
        "worker/requirements.txt"
    )
    
    foreach ($file in $requiredFiles) {
        if (-not (Test-Path $file)) {
            Write-Host "❌ Missing: $file" -ForegroundColor Red
            exit 1
        }
    }
    
    Write-Host "✅ All required files found`n"
}

# Initialize git repository
function Init-Git {
    Write-Host "Initializing Git repository..."
    
    if (Test-Path .git) {
        Write-Host "⚠️  Git repository already exists, skipping init"
    }
    else {
        git init | Out-Null
        Write-Host "✅ Git initialized`n"
    }
}

# Create comprehensive .gitignore
function Create-Gitignore {
    Write-Host "Creating .gitignore..."
    
    $gitignore = @"
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
*`$py.class
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
"@
    
    Set-Content -Path .gitignore -Value $gitignore
    Write-Host "✅ .gitignore created`n"
}

# Add all files
function Add-Files {
    Write-Host "Adding files to Git..."
    
    git add . | Out-Null
    
    $fileCount = (git ls-files | Measure-Object -Line).Lines
    Write-Host "✅ $fileCount files staged for commit`n"
}

# Create initial commit
function Create-Commit {
    Write-Host "Creating initial commit..."
    
    $commitMessage = @"
Initial commit: Kids Animation Pipeline - All phases complete

- Phase 1: Story generation (Ollama LLM)
- Phase 2: Text-to-speech (eSpeak-ng)
- Phase 3: Visual generation & video composition (FFmpeg)
- Phase 4: Background music framework
- Phase 5: n8n automation ready
- Phase 6: YouTube OAuth integration
- Phase 7: Error handling & logging
- 3 GitHub Actions workflows
- Complete documentation
- Tested & verified
"@
    
    git commit -m $commitMessage | Out-Null
    Write-Host "✅ Initial commit created`n"
}

# Configure remote
function Configure-Remote {
    Write-Host "Configuring remote repository..."
    
    try {
        $remoteUrl = git remote get-url origin 2>$null
        if ($remoteUrl) {
            Write-Host "ℹ️  Remote 'origin' already configured"
            Write-Host "    URL: $remoteUrl`n"
            return $true
        }
    }
    catch {
        # Remote doesn't exist
    }
    
    if ($GitHubUsername) {
        $remoteUrl = "https://github.com/$GitHubUsername/$RepositoryName.git"
        
        Write-Host "Adding remote repository..."
        Write-Host "URL: $remoteUrl"
        
        git remote add origin $remoteUrl
        Write-Host "✅ Remote configured`n"
        return $true
    }
    else {
        Write-Host "⚠️  GitHub username not provided`n"
        Write-Host "To configure remote, run:"
        Write-Host "  .\push-to-github.ps1 -GitHubUsername YOUR-USERNAME`n"
        return $false
    }
}

# Push to GitHub
function Push-ToGitHub {
    Write-Host "Pushing to GitHub..."
    
    git branch -M main | Out-Null
    git push -u origin main 2>&1 | Write-Host
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Code pushed to GitHub!`n"
        return $true
    }
    else {
        Write-Host "❌ Push failed. Check your credentials.`n"
        return $false
    }
}

# Enable GitHub Actions
function Enable-Actions {
    Write-Host "════════════════════════════════════════════════════════════════"
    Write-Host "Enabling GitHub Actions..."
    Write-Host "════════════════════════════════════════════════════════════════`n"
    
    Write-Host "To enable GitHub Actions:"
    Write-Host "1. Go to: https://github.com/$GitHubUsername/$RepositoryName/settings"
    Write-Host "2. Left sidebar: Actions → General"
    Write-Host "3. Under 'Actions permissions': Select 'Allow all actions...'"
    Write-Host "4. Click Save"
    Write-Host ""
    Write-Host "5. Go to Actions tab to see workflows"
    Write-Host "`n"
}

# Main execution
function Main {
    Check-Files
    Init-Git
    Create-Gitignore
    Add-Files
    Create-Commit
    
    $remoteConfigured = Configure-Remote
    
    if ($remoteConfigured) {
        $pushSuccess = Push-ToGitHub
        
        if ($pushSuccess -and $GitHubUsername) {
            Enable-Actions
        }
    }
    
    Write-Host "════════════════════════════════════════════════════════════════"
    Write-Host "✅ GIT SETUP COMPLETE"
    Write-Host "════════════════════════════════════════════════════════════════`n"
    
    Write-Host "Next steps:"
    Write-Host "1. Create GitHub repository: https://github.com/new"
    Write-Host "   Name: kids-animation-pipeline"
    Write-Host "   DO NOT initialize with README"
    Write-Host ""
    Write-Host "2. Run this script with your username:"
    Write-Host "   .\push-to-github.ps1 -GitHubUsername YOUR-USERNAME`n"
    Write-Host "3. Confirm push to GitHub"
    Write-Host "4. Enable GitHub Actions (see above)"
    Write-Host "5. Workflows run automatically!`n"
}

Main
