#!/usr/bin/env bash
# pr.sh — create pull request, watch every check, squash-merge (deterministic bytes)
# Usage: scripts/pr.sh [--title "…"] [--body "…" | --body-file FILE] [--base main] [--head BRANCH] [--watch] [--merge|--no-merge] [--draft]
#   --watch : poll EVERY check on the PR until all pass; on failure dump logs and exit 1 for the model to fix
#   --merge : after a green watch, squash-merge (waits for mergeable_state clean; refuses otherwise)
# Squash body defaults to the PR body, so the Co-authored-by provenance trailer survives the squash.
# Env: GH_TOKEN via gh auth. PR URL on stdout, progress on stderr. Fails loud, no secrets in logs.
# Exit: 0 ok | 1 checks failed or merge refused | 2 usage or unusable head ref
set -euo pipefail

# ${BASH_SOURCE[0]}, not $0: the tests source this file to exercise its pure functions, and
# under `source` $0 is the caller's shell, so $0 would resolve LIB_DIR against the wrong tree.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$(cd "$SCRIPT_DIR/../../../lib" && pwd)"
# Repo identity from its single authority — see lib/repo.sh for why `gh repo view` is unsafe here.
# shellcheck source=../../../lib/repo.sh
source "$LIB_DIR/repo.sh"
# Check verdict from its single authority — see lib/checks.sh.
# shellcheck source=../../../lib/checks.sh
source "$LIB_DIR/checks.sh"

# Poll budget 60 × 10s: the harness repo's own test job runs ~4 min, so the previous 30 × 10s
# sat one slow run away from a spurious timeout.
POLL_TRIES=60
POLL_INTERVAL=10
MERGE_STATE_TRIES=5
MERGE_STATE_INTERVAL=2

BASE=""
HEAD_REF=""
TITLE=""
TITLE_SUPPLIED=0
BODY=""
BODY_SUPPLIED=0
BODY_FILE=""
WATCH=0
MERGE=0
DRAFT=0
REPO=""
NUM=""

usage() { sed -n '2,10p' "$0"; }

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
    --base)
      BASE="$2"
      shift 2
      ;;
    --head)
      HEAD_REF="$2"
      shift 2
      ;;
    --title)
      TITLE="$2"
      TITLE_SUPPLIED=1
      shift 2
      ;;
    --body)
      BODY="$2"
      BODY_SUPPLIED=1
      shift 2
      ;;
    --body-file)
      BODY_FILE="$2"
      BODY_SUPPLIED=1
      shift 2
      ;;
    --watch)
      WATCH=1
      shift
      ;;
    --no-watch)
      WATCH=0
      shift
      ;;
    --merge)
      MERGE=1
      shift
      ;;
    --no-merge)
      MERGE=0
      shift
      ;;
    --draft)
      DRAFT=1
      shift
      ;;
    --no-draft)
      DRAFT=0
      shift
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      echo "unknown arg: $1" >&2
      exit 2
      ;;
    esac
  done
}

resolve_head() {
  [[ -n "$HEAD_REF" ]] || HEAD_REF=$(git rev-parse --abbrev-ref HEAD)
  if [[ "$HEAD_REF" == "HEAD" || "$HEAD_REF" == "main" ]]; then
    echo "refusing to open PR from $HEAD_REF" >&2
    exit 2
  fi
}

resolve_title_and_body() {
  [[ -n "$TITLE" ]] || TITLE=$(git log -1 --pretty=%s)
  if [[ -n "$BODY_FILE" ]]; then
    if [[ ! -f "$BODY_FILE" || ! -r "$BODY_FILE" ]]; then
      echo "body file not found or not readable: $BODY_FILE" >&2
      exit 2
    fi
    BODY=$(cat "$BODY_FILE")
  fi
}

resolve_repo() {
  if ! REPO=$(repo_slug); then
    echo "cannot resolve repo slug (no GitHub remote for branch/origin)" >&2
    exit 2
  fi
}

# Ask the repo we resolved from the push remote, then the local remote HEAD, then main.
resolve_base() {
  [[ -n "$BASE" ]] && return 0
  BASE=$(default_branch) || BASE=""
  if [[ -z "$BASE" ]]; then
    BASE=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@origin/@@')
  fi
  [[ -n "$BASE" ]] || BASE="main"
}

create_or_reuse_pr() {
  local existing resp draft_flag="false"
  existing=$(gh api "repos/$REPO/pulls?head=${REPO%%/*}:$HEAD_REF&state=open" --jq '.[0].number' 2>/dev/null || echo "")
  if [[ -n "$existing" && "$existing" != "null" ]]; then
    NUM="$existing"
    echo "found existing PR #$NUM" >&2
    local patch_args=() updated_fields=()
    if [[ $TITLE_SUPPLIED -eq 1 ]]; then
      patch_args+=(-f title="$TITLE")
      updated_fields+=("title")
    else
      local existing_title
      existing_title=$(gh api "repos/$REPO/pulls/$NUM" --jq '.title // empty' 2>/dev/null || echo "")
      [[ -n "$existing_title" ]] && TITLE="$existing_title"
    fi
    if [[ $BODY_SUPPLIED -eq 1 ]]; then
      patch_args+=(-f body="$BODY")
      updated_fields+=("body")
    else
      BODY=$(gh api "repos/$REPO/pulls/$NUM" --jq '.body // ""' 2>/dev/null || echo "")
    fi
    if [[ ${#patch_args[@]} -gt 0 ]]; then
      gh api "repos/$REPO/pulls/$NUM" -X PATCH "${patch_args[@]}" >/dev/null || true
      local fields_str
      fields_str=$(IFS=', '; echo "${updated_fields[*]}")
      echo "updating PR #$NUM: $fields_str" >&2
    fi
    return 0
  fi
  if [[ $DRAFT -eq 1 ]]; then draft_flag="true"; fi
  if [[ $BODY_SUPPLIED -eq 0 && -z "$BODY" && -f .github/pull_request_template.md ]]; then
    BODY=$(cat .github/pull_request_template.md)
  fi
  # `--jq` replaces the previous external `jq -r .number`, so this script needs only gh + git.
  resp=$(gh api "repos/$REPO/pulls" -X POST -f title="$TITLE" -f head="$HEAD_REF" -f base="$BASE" \
    -f body="$BODY" -F draft="$draft_flag" --jq '.number')
  NUM="$resp"
  echo "created PR #$NUM" >&2
}

pr_url() { gh api "repos/$REPO/pulls/$NUM" --jq .html_url; }

# checks_payload — `name<TAB>bucket` for EVERY check on the PR (gh merges check runs and commit
# statuses). gh exits non-zero when a PR has no checks yet, so only a non-empty payload is
# trusted; an empty result stays empty and the verdict reads that as pending, never success.
checks_payload() {
  local payload
  payload=$(gh pr checks "$NUM" --repo "$REPO" --json name,bucket --jq '.[] | [.name,.bucket] | @tsv' 2>/dev/null) || true
  printf '%s\n' "${payload:-}"
}

dump_failure_logs() {
  local sha run_id
  sha=$(gh api "repos/$REPO/pulls/$NUM" --jq .head.sha 2>/dev/null || echo "")
  run_id=""
  if [[ -n "$sha" ]]; then
    run_id=$(gh api "repos/$REPO/actions/runs?head_sha=$sha&per_page=1" --jq '.workflow_runs[0].id // empty' 2>/dev/null || echo "")
  fi
  if [[ -n "$run_id" ]]; then
    gh run view "$run_id" --repo "$REPO" --log 2>&1 | tail -n 200 >&2 || true
  fi
  gh pr checks "$NUM" --repo "$REPO" 2>&1 | tail -n 50 >&2 || true
}

pr_conflict_verdict() {
  local mergeable="${1:-}" state="${2:-}"
  case "$mergeable" in
  false | CONFLICTING)
    printf 'conflicting'
    return 0
    ;;
  esac
  case "$state" in
  dirty | DIRTY)
    printf 'conflicting'
    return 0
    ;;
  behind | BEHIND)
    printf 'behind'
    return 0
    ;;
  unknown | UNKNOWN | "")
    printf 'unknown'
    return 0
    ;;
  *)
    if [[ "$mergeable" == "null" || -z "$mergeable" ]]; then
      printf 'unknown'
    else
      printf 'clean'
    fi
    ;;
  esac
}

check_conflicts() {
  local line mergeable state url files tries=3 verdict=""
  while ((tries-- > 0)); do
    line=$(gh api "repos/$REPO/pulls/$NUM" --jq '[(if .mergeable == null then "null" else (.mergeable|tostring) end), (.mergeable_state // "unknown"), (.html_url // "")] | @tsv' 2>/dev/null || echo "")
    [[ -n "$line" ]] || return 0
    IFS=$'\t' read -r mergeable state url <<<"$line"
    verdict=$(pr_conflict_verdict "$mergeable" "$state")
    if [[ "$verdict" != "unknown" ]]; then
      break
    fi
    sleep 1
  done

  if [[ "$verdict" == "conflicting" ]]; then
    files=$(gh pr view "$NUM" --repo "$REPO" --json files --jq '[.files[].path] | join(" ")' 2>/dev/null || echo "")
    echo "PR $url" >&2
    echo "conflicting: mergeable=$mergeable merge_state_status=$state" >&2
    [[ -n "$files" ]] && echo "files: $files" >&2
    echo "resolve: merge or rebase origin/$BASE into the head branch, then re-run" >&2
    return 1
  fi
  if [[ "$verdict" == "behind" ]]; then
    echo "warning: head branch is behind $BASE" >&2
  fi
  return 0
}

watch_checks() {
  local i verdict
  for ((i = 1; i <= POLL_TRIES; i++)); do
    if ! check_conflicts; then
      return 1
    fi
    verdict=$(checks_payload | checks_verdict)
    case "$verdict" in
    success)
      echo "checks success" >&2
      return 0
      ;;
    failure)
      echo "checks failed — fetching logs" >&2
      dump_failure_logs
      return 1
      ;;
    *)
      echo "checks pending ($i/$POLL_TRIES)…" >&2
      sleep "$POLL_INTERVAL"
      ;;
    esac
  done
  echo "checks timeout after $((POLL_TRIES * POLL_INTERVAL))s — no green verdict" >&2
  gh pr checks "$NUM" --repo "$REPO" 2>&1 | tail -n 30 >&2 || true
  return 1
}

# squash_message — body of the squash commit. Defaults to the PR body, which is where the
# `Co-authored-by` trailer lives. If the PR body is empty or identical to the repo's PR
# template, returns empty so GitHub squash-merge defaults to commit subjects.
squash_message() {
  local template=""
  if [[ -f .github/pull_request_template.md ]]; then
    template=$(cat .github/pull_request_template.md)
  fi
  local trimmed_body="${BODY%"${BODY##*[![:space:]]}"}"
  local trimmed_template="${template%"${template##*[![:space:]]}"}"
  if [[ -z "$trimmed_body" || ( -n "$trimmed_template" && "$trimmed_body" == "$trimmed_template" ) ]]; then
    return 0
  fi
  printf '%s' "$BODY"
}

merge_pr() {
  local i state=""
  for ((i = 1; i <= MERGE_STATE_TRIES; i++)); do
    state=$(gh api "repos/$REPO/pulls/$NUM" --jq .mergeable_state 2>/dev/null || echo unknown)
    if [[ "$state" == "clean" ]]; then break; fi
    echo "mergeable_state=$state waiting…" >&2
    sleep "$MERGE_STATE_INTERVAL"
  done
  # Refuse rather than merge through a dirty/blocked state: this is the same failure class as
  # watching the wrong checks — the merge must not outrun its evidence.
  if [[ "$state" != "clean" ]]; then
    echo "refusing to merge: mergeable_state=$state (not clean)" >&2
    return 1
  fi
  local merge_args=(-f merge_method=squash -f commit_title="$TITLE (#$NUM)")
  local msg
  msg=$(squash_message)
  if [[ -n "$msg" ]]; then
    merge_args+=(-f commit_message="$msg")
  fi
  gh api "repos/$REPO/pulls/$NUM/merge" -X PUT "${merge_args[@]}" >/dev/null
  echo "merged #$NUM (squash) to $BASE" >&2
}

main() {
  parse_args "$@"
  resolve_head
  resolve_title_and_body
  resolve_repo
  resolve_base
  create_or_reuse_pr
  echo "PR $(pr_url)"

  if [[ $WATCH -eq 1 ]]; then
    if ! watch_checks; then
      exit 1
    fi
  fi

  if [[ $MERGE -eq 1 ]]; then
    # --merge implies a green watch: merging is unreachable without one, even with --no-watch.
    if [[ $WATCH -eq 0 ]]; then
      if ! watch_checks; then exit 1; fi
    fi
    if ! merge_pr; then exit 1; fi
  fi
}

# Sourced for tests: only define, never act.
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
