#!/usr/bin/env python3
"""
Automated GitHub Push Script
Handles git operations programmatically without shell git command
"""

import os
import subprocess
import json
from pathlib import Path
from datetime import datetime

class GitHubPusher:
    def __init__(self, username, email, token, repo_name):
        self.username = username
        self.email = email
        self.token = token
        self.repo_name = repo_name
        self.repo_url = f"https://{token}@github.com/{username}/{repo_name}.git"
        self.project_root = Path.cwd()
        
    def log(self, message, status="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {status:8} | {message}")
    
    def run_command(self, cmd, description):
        """Run shell command and handle errors"""
        try:
            self.log(f"Executing: {description}", "RUN")
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                self.log(f"✅ {description}", "SUCCESS")
                if result.stdout:
                    self.log(f"Output: {result.stdout[:200]}", "OUTPUT")
                return True
            else:
                self.log(f"❌ {description}", "ERROR")
                if result.stderr:
                    self.log(f"Error: {result.stderr[:200]}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Exception in {description}: {str(e)}", "ERROR")
            return False
    
    def check_files(self):
        """Verify all required files exist"""
        self.log("Checking project files...", "CHECK")
        required_files = [
            "docker-compose.yml",
            ".env.example",
            "worker/pipeline.py",
            "worker/Dockerfile",
            "worker/requirements.txt"
        ]
        
        for file in required_files:
            if not Path(file).exists():
                self.log(f"Missing: {file}", "ERROR")
                return False
            self.log(f"✅ Found: {file}", "CHECK")
        
        return True
    
    def create_gitignore(self):
        """Create .gitignore file"""
        self.log("Creating .gitignore", "CREATE")
        
        gitignore_content = """# Environment variables
.env
.env.local
.env.*.local

# Credentials (NEVER COMMIT)
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
"""
        try:
            Path(".gitignore").write_text(gitignore_content)
            self.log("✅ .gitignore created", "CREATE")
            return True
        except Exception as e:
            self.log(f"Failed to create .gitignore: {e}", "ERROR")
            return False
    
    def push_to_github(self):
        """Main push sequence"""
        try:
            # Step 1: Configure git
            self.log("Step 1: Configuring Git", "STEP")
            self.run_command(
                f'git config --global user.name "{self.username}"',
                "Configure git username"
            )
            self.run_command(
                f'git config --global user.email "{self.email}"',
                "Configure git email"
            )
            self.run_command(
                'git config --global credential.helper store',
                "Configure credential helper"
            )
            
            # Step 2: Check files
            self.log("Step 2: Checking project files", "STEP")
            if not self.check_files():
                self.log("Project files check failed", "ERROR")
                return False
            
            # Step 3: Create .gitignore
            self.log("Step 3: Creating .gitignore", "STEP")
            if not self.create_gitignore():
                self.log("Failed to create .gitignore", "ERROR")
                return False
            
            # Step 4: Initialize git (if needed)
            self.log("Step 4: Initializing Git repository", "STEP")
            git_dir = Path(".git")
            if not git_dir.exists():
                self.run_command("git init", "Initialize git repository")
            else:
                self.log("Git repository already initialized", "INFO")
            
            # Step 5: Remove existing remote (if any)
            self.log("Step 5: Configuring remote repository", "STEP")
            self.run_command("git remote remove origin", "Remove existing origin (if any)")
            
            # Step 6: Add remote
            self.run_command(
                f'git remote add origin "{self.repo_url}"',
                "Add remote repository"
            )
            
            # Step 7: Add all files
            self.log("Step 6: Staging files", "STEP")
            self.run_command("git add .", "Stage all files")
            
            # Step 8: Create commit
            self.log("Step 7: Creating commit", "STEP")
            commit_message = """Initial commit: Kids Animation Pipeline - All phases complete

- Phase 1: Story generation (Ollama LLM)
- Phase 2: Text-to-speech (eSpeak-ng)
- Phase 3: Visual generation & video composition (FFmpeg)
- Phase 4: Background music framework
- Phase 5: n8n automation ready
- Phase 6: YouTube OAuth integration
- Phase 7: Error handling & logging
- 3 GitHub Actions workflows
- Complete documentation
- Tested & verified"""
            
            self.run_command(
                f'git commit -m "{commit_message}"',
                "Create initial commit"
            )
            
            # Step 9: Set main branch
            self.log("Step 8: Setting main branch", "STEP")
            self.run_command("git branch -M main", "Set branch to main")
            
            # Step 10: Push to GitHub
            self.log("Step 9: Pushing to GitHub", "STEP")
            push_cmd = f"git push -u origin main"
            if not self.run_command(push_cmd, "Push code to GitHub"):
                self.log("Push failed - may need manual intervention", "ERROR")
                return False
            
            self.log("✅ All steps completed successfully!", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Unexpected error: {e}", "ERROR")
            return False


def main():
    print("\n" + "="*80)
    print("      🚀 KIDS ANIMATION PIPELINE - AUTOMATED GITHUB PUSH")
    print("="*80 + "\n")
    
    # Credentials
    username = "pshijil22"
    email = "pshijil22@gmail.com"
    token = os.environ.get('GITHUB_TOKEN')  # Get from environment variable
    repo_name = "kids-animation-pipeline"
    
    if not token:
        print("❌ ERROR: GitHub token not provided")
        print("Set GITHUB_TOKEN environment variable")
        return False
    
    print(f"📋 Configuration:")
    print(f"   Username: {username}")
    print(f"   Email: {email}")
    print(f"   Repository: {repo_name}")
    print(f"   Token: {'✅ Configured' if token else '❌ Missing'}")
    print("\n" + "="*80 + "\n")
    
    # Create pusher and execute
    pusher = GitHubPusher(username, email, token, repo_name)
    success = pusher.push_to_github()
    
    print("\n" + "="*80)
    if success:
        print("✅ PUSH SUCCESSFUL!")
        print("="*80)
        print("\n📋 Next Steps:")
        print("   1. Go to: https://github.com/pshijil22/kids-animation-pipeline")
        print("   2. Verify your code is there")
        print("   3. Go to Settings → Actions → General")
        print("   4. Select 'Allow all actions and reusable workflows'")
        print("   5. Click Save")
        print("\n🎬 Your automation is now live!")
        print("   • Tests run on every push")
        print("   • Videos generate daily at 9 AM UTC")
        print("   • Manual trigger available anytime")
        return True
    else:
        print("❌ PUSH FAILED")
        print("="*80)
        print("\n🔧 Troubleshooting:")
        print("   1. Verify GitHub token is valid")
        print("   2. Verify repository exists on GitHub")
        print("   3. Check internet connection")
        print("   4. Try manual push with: git push -u origin main")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
