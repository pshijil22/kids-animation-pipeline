#!/bin/sh
cd /repo
git config --global user.name "pshijil22"
git config --global user.email "pshijil22@gmail.com"
git config --global credential.useHttpPath true
git remote set-url origin "https://pshijil22:$1@github.com/pshijil22/kids-animation-pipeline.git"
echo "🚀 Pushing code..."
git push -u origin main
echo "✅ DONE"
