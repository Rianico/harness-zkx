#!/usr/bin/env bash
set -euo pipefail
# Dispatch semantic-release via GitHub dispatch or dry-run preview
# Usage: dispatch.sh [--dry-run]
DRY=""
if [[ "${1:-}" == "--dry-run" ]]; then DRY="--dry-run"; fi
if [ -n "$DRY" ]; then
  GITHUB_TOKEN=$(gh auth token) npx semantic-release --dry-run
  exit 0
fi
# Preview version
GITHUB_TOKEN=$(gh auth token) npx semantic-release --dry-run || true
read -r -p "a: dispatch b: hold > " ans
if [ "$ans" != "a" ]; then
  echo "hold"
  exit 0
fi
OWNER_REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
gh api repos/$OWNER_REPO/dispatches -f event_type=semantic-release
echo "dispatched $OWNER_REPO"
