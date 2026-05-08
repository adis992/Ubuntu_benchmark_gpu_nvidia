#!/bin/bash

# Push to GitHub Script
# Use this to push your code to GitHub

echo "================================================"
echo "📤 Push to GitHub"
echo "================================================"
echo ""

# Check if remote exists
if ! git remote | grep -q "origin"; then
    echo "❌ GitHub remote repository not configured yet."
    echo ""
    echo "To push to GitHub, you need to:"
    echo ""
    echo "1. Create a new repository on GitHub:"
    echo "   https://github.com/new"
    echo ""
    echo "2. Then run ONE of these commands:"
    echo ""
    echo "   # For HTTPS (easier):"
    echo "   git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git"
    echo ""
    echo "   # For SSH (more secure):"
    echo "   git remote add origin git@github.com:YOUR_USERNAME/REPO_NAME.git"
    echo ""
    echo "3. Then run this script again:"
    echo "   ./push_to_github.sh"
    echo ""
    echo "================================================"
    echo ""
    echo "Quick example:"
    echo "  git remote add origin https://github.com/noname/nvidia-benchmark.git"
    echo "  ./push_to_github.sh"
    echo ""
    exit 1
fi

# Get remote URL
REMOTE_URL=$(git remote get-url origin)

echo "✓ Remote configured: $REMOTE_URL"
echo ""

# Check if we have commits
if ! git log &>/dev/null; then
    echo "❌ No commits to push"
    echo ""
    echo "Run: git commit -m 'Your message'"
    exit 1
fi

# Get current branch
BRANCH=$(git branch --show-current)

echo "📊 Current status:"
git status -sb
echo ""

# Ask for confirmation
read -p "Push to $REMOTE_URL on branch '$BRANCH'? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Push cancelled"
    exit 0
fi

echo ""
echo "🚀 Pushing to GitHub..."
echo ""

# Set upstream and push
git push -u origin "$BRANCH"

if [ $? -eq 0 ]; then
    echo ""
    echo "================================================"
    echo "✅ Successfully pushed to GitHub!"
    echo "================================================"
    echo ""
    echo "Repository: $REMOTE_URL"
    echo "Branch: $BRANCH"
    echo ""
    echo "View your code at:"
    echo "  ${REMOTE_URL%.git}"
    echo ""
else
    echo ""
    echo "================================================"
    echo "❌ Push failed"
    echo "================================================"
    echo ""
    echo "Common issues:"
    echo ""
    echo "1. Authentication failed:"
    echo "   - For HTTPS: GitHub removed password auth"
    echo "   - Use Personal Access Token instead"
    echo "   - Or switch to SSH"
    echo ""
    echo "2. Permission denied:"
    echo "   - Make sure you own the repository"
    echo "   - Check your GitHub username in the URL"
    echo ""
    echo "3. Repository doesn't exist:"
    echo "   - Create it on GitHub first"
    echo "   - https://github.com/new"
    echo ""
    exit 1
fi
