#!/usr/bin/env bash
# pr.sh — create PR, watch verify, and squash-merge via gh api (git scaffolding, deterministic bytes)
# Usage: scripts/pr.sh [--title "…"] [--body "…" | --body-file FILE] [--base main] [--head BRANCH] [--watch] [--merge|--no-merge] [--draft]
#   --watch : poll checks (verify/changelog-check) until success; on failure dumps logs and exits 1 for model to fix
#   --merge : after watch success, squash-merge (waits for mergeable_state clean)
# Env: GH_TOKEN via gh auth. Fails loud, no secrets in logs.
set -euo pipefail

BASE=""; HEAD_REF=""; TITLE=""; BODY=""; BODY_FILE=""; WATCH=0; MERGE=0; DRAFT=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --base) BASE="$2"; shift 2;;
    --head) HEAD_REF="$2"; shift 2;;
    --title) TITLE="$2"; shift 2;;
    --body) BODY="$2"; shift 2;;
    --body-file) BODY_FILE="$2"; shift 2;;
    --watch) WATCH=1; shift;;
    --no-watch) WATCH=0; shift;;
    --merge) MERGE=1; shift;;
    --no-merge) MERGE=0; shift;;
    --draft) DRAFT=1; shift;;
    --no-draft) DRAFT=0; shift;;
    -h|--help) sed -n '2,10p' "$0"; exit 0;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done

if [[ -z "$HEAD_REF" ]]; then HEAD_REF=$(git rev-parse --abbrev-ref HEAD); fi
if [[ "$HEAD_REF" == "HEAD" || "$HEAD_REF" == "main" ]]; then echo "refusing to open PR from $HEAD_REF" >&2; exit 2; fi
if [[ -z "$BASE" ]]; then
  if BASE=$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name 2>/dev/null) && [[ -n "$BASE" ]]; then :;
  elif BASE=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@origin/@@'); then :;
  else BASE="main"; fi
fi
if [[ -z "$TITLE" ]]; then TITLE=$(git log -1 --pretty=%s); fi
if [[ -n "$BODY_FILE" ]]; then BODY=$(cat "$BODY_FILE"); fi
if [[ -z "$BODY" ]]; then
  if [[ -f .github/pull_request_template.md ]]; then BODY=$(cat .github/pull_request_template.md); else BODY=""; fi
fi

REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || git remote get-url origin | sed -E 's@.*github\\.com[:/]([^/]+/[^/.]+)(\\.git)?@\\1@')
echo "repo=$REPO head=$HEAD_REF base=$BASE watch=$WATCH merge=$MERGE" >&2

EXISTING=$(gh api "repos/$REPO/pulls?head=${REPO%%/*}:$HEAD_REF&state=open" --jq '.[0].number' 2>/dev/null || echo "")
if [[ -n "$EXISTING" && "$EXISTING" != "null" ]]; then
  NUM="$EXISTING"
  echo "found existing PR #$NUM" >&2
  if [[ -n "$TITLE" || -n "$BODY" ]]; then
    gh api "repos/$REPO/pulls/$NUM" -X PATCH -f title="$TITLE" -f body="$BODY" >/dev/null || true
  fi
else
  DRAFT_FLAG="false"; [[ $DRAFT -eq 1 ]] && DRAFT_FLAG="true"
  RESP=$(gh api "repos/$REPO/pulls" -X POST -f title="$TITLE" -f head="$HEAD_REF" -f base="$BASE" -f body="$BODY" -F draft="$DRAFT_FLAG")
  NUM=$(echo "$RESP" | jq -r .number)
  echo "created PR #$NUM" >&2
fi

URL=$(gh api "repos/$REPO/pulls/$NUM" --jq .html_url)
echo "PR $URL"

# resolve head SHA for check runs
SHA=$(gh api "repos/$REPO/pulls/$NUM" --jq .head.sha)
echo "sha=$SHA" >&2

watch_checks() {
  local num="$1" sha="$2" tries=30
  for ((i=1;i<=tries;i++)); do
    # prefer check-runs, fallback to pr checks
    STATE=$(gh api "repos/$REPO/commits/$sha/check-runs?per_page=100" --jq '[.check_runs[] | select(.name=="verify" or .name=="check" or .name=="changelog-check")] | if length==0 then "pending" elif any(.conclusion=="failure" or .conclusion=="timed_out" or .conclusion=="cancelled") then "failure" elif any(.status!="completed") then "pending" else "success" end' 2>/dev/null || echo "pending")
    if [[ "$STATE" == "success" ]]; then echo "checks success" >&2; return 0; fi
    if [[ "$STATE" == "failure" ]]; then
      echo "checks failed — fetching logs" >&2
      RUN_ID=$(gh api "repos/$REPO/commits/$sha/check-runs?per_page=100" --jq '.check_runs[] | select(.conclusion=="failure") | .id' 2>/dev/null | head -1)
      # also try actions runs
      if [[ -z "$RUN_ID" ]]; then
        RUN_ID=$(gh api "repos/$REPO/actions/runs?head_sha=$sha&per_page=1" --jq '.workflow_runs[0].id' 2>/dev/null || echo "")
      fi
      if [[ -n "$RUN_ID" && "$RUN_ID" != "null" ]]; then
        gh run view "$RUN_ID" --log 2>&1 | tail -n 200 >&2 || true
        gh api "repos/$REPO/actions/runs/$RUN_ID/logs" 2>&1 | tail -n 20 >&2 || true
      fi
      gh pr checks "$num" --json state,conclusion 2>&1 | tail -n 50 >&2 || true
      return 1
    fi
    echo "checks $STATE ($i/$tries)…" >&2
    sleep 10
  done
  echo "checks timeout" >&2; return 1
}

if [[ $WATCH -eq 1 ]]; then
  if ! watch_checks "$NUM" "$SHA"; then
    echo "watch failed — fix and re-run: scripts/pr.sh --watch --merge (or git push then re-run)" >&2
    exit 1
  fi
fi

if [[ $MERGE -eq 1 ]]; then
  # ensure watch passed if not already
  if [[ $WATCH -eq 0 ]]; then
    if ! watch_checks "$NUM" "$SHA"; then exit 1; fi
  fi
  for i in 1 2 3 4 5; do
    STATE=$(gh api "repos/$REPO/pulls/$NUM" --jq .mergeable_state 2>/dev/null || echo "unknown")
    if [[ "$STATE" == "clean" ]]; then break; fi
    echo "mergeable_state=$STATE waiting…" >&2; sleep 2
  done
  gh api "repos/$REPO/pulls/$NUM/merge" -X PUT -f merge_method=squash -f commit_title="$TITLE (#$NUM)" -f commit_message="Squash merge $HEAD_REF → $BASE" >/dev/null
  echo "merged #$NUM (squash) to $BASE" >&2
fi
