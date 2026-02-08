#!/bin/bash
# Script: Push current branch, merge to main, return to current branch

set -e  # Exit on error

# Get current branch name
CURRENT_BRANCH=$(git branch --show-current)

echo "📍 Current branch: $CURRENT_BRANCH"

# Check for uncommitted changes
if [[ -n $(git status --porcelain) ]]; then
    echo "⚠️  Uncommitted changes detected. Committing..."
    git add -A
    read -p "Commit message: " COMMIT_MSG
    git commit -m "$COMMIT_MSG"
fi

# Push current branch
echo "⬆️  Pushing $CURRENT_BRANCH..."
git push origin "$CURRENT_BRANCH"

# Switch to main and merge
echo "🔀 Switching to main..."
git checkout main

echo "⬇️  Pulling latest main..."
git pull origin main

echo "🔀 Merging $CURRENT_BRANCH into main..."
git merge "$CURRENT_BRANCH" --no-edit

echo "⬆️  Pushing main..."
git push origin main

# Return to original branch
echo "↩️  Returning to $CURRENT_BRANCH..."
git checkout "$CURRENT_BRANCH"

echo "✅ Done! $CURRENT_BRANCH merged to main and pushed."
