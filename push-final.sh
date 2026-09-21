#!/bin/sh
set -e

TOKEN="$1"
cd /repo

echo "📋 Configuring Git..."
git config --global user.name "pshijil22"
git config --global user.email "pshijil22@gmail.com"

echo "📋 Setting remote URL..."
git remote remove origin 2>/dev/null || true
git remote add origin "https://pshijil22:${TOKEN}@github.com/pshijil22/kids-animation-pipeline.git"

echo "📋 Verifying remote..."
git remote -v

echo ""
echo "🚀 Pushing to GitHub..."
if git push -u origin main 2>&1; then
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                  ✅ PUSH SUCCESSFUL! ✅                       ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "🎉 Your code is now on GitHub!"
    echo ""
    echo "📋 Next Steps:"
    echo "   1. Go to: https://github.com/pshijil22/kids-animation-pipeline"
    echo "   2. Verify your code is there"
    echo "   3. Go to Settings → Actions → General"
    echo "   4. Select 'Allow all actions and reusable workflows'"
    echo "   5. Click Save"
    echo ""
    echo "🎬 Your automation will then:"
    echo "   • Run tests on every push"
    echo "   • Generate videos daily at 9 AM UTC"
    echo "   • Allow manual generation anytime"
    exit 0
else
    echo ""
    echo "❌ Push failed"
    exit 1
fi
