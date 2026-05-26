#!/usr/bin/env bash
# cos-push.sh — commit and push cos personal OS changes
# Usage: cos-push.sh ["commit message"]
# Default message is timestamped if none provided.

set -e

REPO="/Users/n1/Projects/cos"
MSG="${1:-"cos update $(date '+%Y-%m-%d %H:%M')"}"

cd "$REPO"

# Clear any stale lock from a crashed git process
if [ -f .git/index.lock ]; then
  echo "⚠  Removing stale .git/index.lock"
  rm -f .git/index.lock
fi

echo "📂 Status:"
git status --short

# Stage everything (respects .gitignore — data/, inputs/, memory personal files stay out)
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
