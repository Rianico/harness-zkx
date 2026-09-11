#!/usr/bin/env bash
# release-watch.sh — dispatch semantic-release and watch workflow (deterministic bytes)
# Usage: scripts/release-watch.sh [--watch] [--timeout 600]
#   dispatches via repository_dispatch (or workflow_dispatch) then polls actions/runs for release.yml
#   on failure dumps logs and exits 1 for model to fix; on success prints version
set -euo pipefail

WATCH=1; TIMEOUT=600
while [[ $# -gt 0 ]]; do
  case "$1" in
    --watch) WATCH=1; shift;;
    --no-watch) WATCH=0; shift;;
    --timeout) TIMEOUT="$2"; shift 2;;
    -h|--help) sed -n '2,6p' "$0"; exit 0;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"

# Release repo from this checkout's push remote — see repo_slug() in _common.sh for why
# `gh repo view` is unsafe here (upstream/fork remote → wrong release target).
if ! REPO=$(repo_slug); then
  echo "cannot resolve release repo slug (no GitHub remote for branch/origin)" >&2
  exit 2
fi
REF=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")
if [[ "$REF" != "main" ]]; then echo "dispatch from main only (current $REF)" >&2; exit 2; fi
SHA_BEFORE=$(git rev-parse HEAD)

echo "dispatch semantic-release to $REPO@$REF" >&2
# try repository_dispatch, fallback to workflow_dispatch
if ! gh api "repos/$REPO/dispatches" -X POST -f event_type="semantic-release" -F client_payload='{}' 2>/dev/null; then
  gh workflow run release.yml --repo "$REPO" --ref main 2>&1 | tail -n 5 >&2 || true
fi

if [[ $WATCH -eq 0 ]]; then echo "dispatched (no watch)" >&2; exit 0; fi

# capture run id by polling for head_sha > SHA_BEFORE
RUN_ID=""; TRIES=$((TIMEOUT/10))
for ((i=1;i<=TRIES;i++)); do
  RUN_ID=$(gh api "repos/$REPO/actions/workflows/release.yml/runs?per_page=5" --jq ".workflow_runs[] | select(.head_sha!=\"$SHA_BEFORE\") | .id" 2>/dev/null | head -1)
  if [[ -z "$RUN_ID" || "$RUN_ID" == "null" ]]; then
    RUN_ID=$(gh api "repos/$REPO/actions/runs?per_page=5" --jq '.workflow_runs[] | select(.head_branch=="main") | .id' 2>/dev/null | head -1)
  fi
  if [[ -n "$RUN_ID" && "$RUN_ID" != "null" ]]; then break; fi
  sleep 5
done
if [[ -z "$RUN_ID" || "$RUN_ID" == "null" ]]; then echo "no release run found" >&2; exit 1; fi
echo "watch run $RUN_ID" >&2

for ((i=1;i<=TRIES;i++)); do
  STATUS=$(gh api "repos/$REPO/actions/runs/$RUN_ID" --jq .status 2>/dev/null || echo "unknown")
  CONCLUSION=$(gh api "repos/$REPO/actions/runs/$RUN_ID" --jq .conclusion 2>/dev/null || echo "null")
  echo "run $RUN_ID $STATUS $CONCLUSION ($i/$TRIES)" >&2
  if [[ "$STATUS" == "completed" ]]; then
    if [[ "$CONCLUSION" == "success" ]]; then
      echo "release success" >&2
      gh api "repos/$REPO/actions/runs/$RUN_ID" --jq '.html_url' >&2 || true
      # print new version
      git fetch --tags --quiet || true
      git describe --tags --abbrev=0 2>&1 | tail -n 1 || true
      exit 0
    else
      echo "release $CONCLUSION — fetching logs" >&2
      gh run view "$RUN_ID" --repo "$REPO" --log 2>&1 | tail -n 300 >&2 || true
      exit 1
    fi
  fi
  sleep 10
done
echo "release watch timeout" >&2; exit 1
