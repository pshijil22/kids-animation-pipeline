#!/bin/sh
# Create GitHub repo via API and then push

set -e

GITHUB_USERNAME="pshijil22"
GITHUB_TOKEN="$1"
REPO_NAME="kids-animation-pipeline"

if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ Error: GitHub token required"
    exit 1
fi

echo "📋 Step 1: Create repository via GitHub API"

# Try to create repo
RESPONSE=$(curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/user/repos \
  -d "{\"name\":\"$REPO_NAME\",\"description\":\"Free, self-hosted automated children's animation generator\",\"private\":false,\"auto_init\":false}" 2>&1)

echo "$RESPONSE" | grep -q "\"name\":\"$REPO_NAME\"" && echo "✅ Repository created or already exists" || echo "⚠️  Repository API response: $RESPONSE" | head -1

echo ""
echo "📋 Step 2: Push code"

cd /repo

git config --global user.name "$GITHUB_USERNAME"
git config --global user.email "pshijil22@gmail.com"

# Update remote URL with token
REMOTE_URL="https://${GITHUB_TOKEN}@github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"
git remote set-url origin "$REMOTE_URL" || git remote add origin "$REMOTE_URL"

echo "Pushing..."
git push -u origin main

echo ""
echo "✅ PUSH COMPLETE!"
