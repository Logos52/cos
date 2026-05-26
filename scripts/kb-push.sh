#!/usr/bin/env bash
# kb-push.sh — commit and push llm-knowledge-base changes
# Usage: kb-push.sh ["commit message"]
# Default message is timestamped if none provided.

set -e

REPO="/Users/n1/Projects/llm-knowledge-base"
MSG="${1:-"kb update $(date '+%Y-%m-%d %H:%M')"}"

cd "$REPO"

# Clear any stale lock from a crashed git process
if [ -f .git/index.lock ]; then
  echo "⚠  Removing stale .git/index.lock"
  rm -f .git/index.lock
fi

echo "📂 Status:"
git status --short

# Stage everything (respects .gitignore — workbench files stay out)
git add -A

echo ""
echo "📋 Staged:"
git diff --cached --stat

echo ""
read -r -p "Commit with message: \"$MSG\"? [y/N] " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
  echo "Aborted. Nothing committed."
  git restore --staged .
  exit 0
fi

git commit -m "$MSG"
git push

echo ""
echo "✓ Pushed to origin/main"
