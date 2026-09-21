# Automated GitHub Push using Docker (PowerShell)
# Usage: .\docker-push.ps1 -GitHubToken "your_token_here"

param(
    [string]$GitHubToken = "",
    [string]$GitHubUsername = "pshijil22",
    [string]$GitHubEmail = "pshijil22@gmail.com",
    [string]$RepositoryName = "kids-animation-pipeline"
)

Write-Host "`n╔════════════════════════════════════════════════════════════════╗"
Write-Host "║     Kids Animation Pipeline - Docker-Based GitHub Push       ║"
Write-Host "╚════════════════════════════════════════════════════════════════╝`n"

if (-not $GitHubToken) {
    Write-Host "❌ ERROR: GitHub token not provided" -ForegroundColor Red
    Write-Host "Usage: .\docker-push.ps1 -GitHubToken `"your_token_here`""
    exit 1
}

$RepoUrl = "https:/`://${GitHubToken}@github.com/${GitHubUsername}/${RepositoryName}.git"

Write-Host "📋 Configuration:"
Write-Host "   Username: $GitHubUsername"
Write-Host "   Email: $GitHubEmail"
Write-Host "   Repository: $RepositoryName`n"

# Create .gitignore
Write-Host "Creating .gitignore..."
$gitignore = @"
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
"@

Set-Content -Path ".gitignore" -Value $gitignore
Write-Host "✅ .gitignore created`n"

# Create Docker script
$dockerScript = @"
#!/bin/sh
set -e

cd /workspace

echo '📋 Step 1: Configure Git'
git config --global user.name '$GitHubUsername'
git config --global user.email '$GitHubEmail'
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
git remote add origin '$RepoUrl'
echo '✅ Remote configured'
echo ''

echo '📋 Step 4: Stage files'
git add .
FILE_COUNT=`$(git ls-files | wc -l)
echo "✅ Staged `$FILE_COUNT files"
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
"@

Write-Host "Running Git operations in Docker..."
Write-Host ""

$currentPath = (Get-Location).Path
$scriptPath = Join-Path $env:TEMP "push-script-$([System.Guid]::NewGuid().ToString()).sh"
Set-Content -Path $scriptPath -Value $dockerScript -Encoding UTF8

try {
    # Run Docker command
    docker run --rm `
      -v "${currentPath}:/workspace" `
      -e GITHUB_TOKEN="$GitHubToken" `
      alpine/git:latest `
      sh < $scriptPath
    
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -eq 0) {
        Write-Host ""
        Write-Host "╔════════════════════════════════════════════════════════════════╗"
        Write-Host "║                   ✅ PUSH SUCCESSFUL!                         ║"
        Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
        Write-Host ""
        Write-Host "🎉 Your code is now on GitHub!`n"
        Write-Host "📋 Next Steps:" -ForegroundColor Cyan
        Write-Host "   1. Go to: https://github.com/$GitHubUsername/$RepositoryName"
        Write-Host "   2. Verify your code is there"
        Write-Host "   3. Go to Settings → Actions → General"
        Write-Host "   4. Select 'Allow all actions and reusable workflows'"
        Write-Host "   5. Click Save`n"
        Write-Host "🎬 Your automation is now live!" -ForegroundColor Green
        Write-Host "   • Tests run on every push"
        Write-Host "   • Videos generate daily at 9 AM UTC"
        Write-Host "   • Manual trigger available anytime"
    }
    else {
        Write-Host ""
        Write-Host "❌ PUSH FAILED (Exit code: $exitCode)" -ForegroundColor Red
        Write-Host ""
        Write-Host "🔧 Troubleshooting:"
        Write-Host "   1. Verify GitHub token is valid"
        Write-Host "   2. Verify repository exists on GitHub: https://github.com/new"
        Write-Host "   3. Check internet connection"
        Write-Host "   4. Try running again"
    }
}
catch {
    Write-Host "❌ Error running Docker: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Make sure Docker is installed and running"
}
finally {
    if (Test-Path $scriptPath) {
        Remove-Item $scriptPath -Force
    }
}
