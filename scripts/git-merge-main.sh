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
git push fork "$CURRENT_BRANCH"

# Switch to main and merge
echo "🔀 Switching to main..."
git checkout main

echo "⬇️  Pulling latest main..."
git pull fork main

echo "🔀 Merging $CURRENT_BRANCH into main..."
git merge "$CURRENT_BRANCH" --no-edit

echo "⬆️  Pushing main..."
git push fork main

# Return to forkal branch
echo "↩️  Returning to $CURRENT_BRANCH..."
git checkout "$CURRENT_BRANCH"

echo "✅ Done! $CURRENT_BRANCH merged to main and pushed."
