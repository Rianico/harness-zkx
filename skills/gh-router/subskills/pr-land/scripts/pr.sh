#!/usr/bin/env bash
# pr.sh — create pull request, watch every check, squash-merge (deterministic bytes)
# Usage: scripts/pr.sh [--title "…"] [--body "…" | --body-file FILE] [--base main] [--head BRANCH] [--watch] [--merge|--no-merge] [--draft] [--check]
#   --watch : poll EVERY check on the PR until all pass; on failure dump logs and exit 1 for the model to fix
#   --merge : after a green watch, squash-merge (waits for mergeable_state clean; refuses otherwise)
#   --check : dry run — print the Co-authored-by trailers a merge would append, then exit (no PR created)
# Squash body is the PR body plus one Co-authored-by trailer per distinct PR commit author
# except the merger (an explicit commit_message disables GitHub's own auto-attribution, so the
# script rebuilds it). A body still holding the raw CODE_AUTHORS template token, or any line
# over 100 chars (commitlint body-max-line-length), is refused pre-merge.
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

# Attribution rebuild (squash-merge provenance): the merge API consumes commit_message
# verbatim, so GitHub never appends its own co-author trailers when this script merges.
CODE_AUTHORS_TOKEN="CODE_AUTHORS"
SQUASH_LINE_MAX=100

BASE=""
HEAD_REF=""
TITLE=""
TITLE_SUPPLIED=0
BODY=""
BODY_SUPPLIED=0
BODY_FILE=""
WATCH=0
MERGE=0
CHECK=0
DRAFT=0
REPO=""
NUM=""

usage() { sed -n '2,11p' "$0"; }

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
    --check)
      CHECK=1
      shift
      ;;
    --no-check)
      CHECK=0
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

# --- Squash attribution ---
#
# GitHub auto-credits every PR commit author on squash ONLY when it builds the message.
# merge_pr() supplies commit_message explicitly, so GitHub uses it verbatim and the safety
# net stays off: these functions rebuild it. pr_co_author_trailers enumerates commit
# authors (merger excluded); insert_trailers splices trailers ahead of closing lines and
# normalizes pasted duplicates; refuse_raw_token / refuse_long_lines gate the result.
# All pure functions read the message on stdin (or $BODY) and print it on stdout, so the
# tests can pin them without gh or a network. No arrays: /usr/bin/env bash may be 3.2.

# trailer_email_key <line> — lowercase email of a Co-authored-by trailer line, else empty.
trailer_email_key() {
  local key
  key=$(printf '%s' "${1:-}" | grep -iE '^[[:space:]]*co-authored-by:' | sed -nE 's/^[^<]*<([^<>]+)>.*$/\1/p' | tr '[:upper:]' '[:lower:]' | head -n 1 || true)
  printf '%s' "$key"
}

# existing_trailer_emails — lowercase emails of every Co-authored-by line on stdin.
existing_trailer_emails() {
  local line key
  while IFS= read -r line || [[ -n "$line" ]]; do
    key=$(trailer_email_key "$line")
    if [[ -n "$key" ]]; then
      printf '%s\n' "$key"
    fi
  done || true
}

# list_contains <newline-list> <key> — exact-line membership (keys pre-folded by callers).
list_contains() {
  [[ -n "${2:-}" ]] || return 1
  printf '%s\n' "$1" | grep -Fxq -- "$2"
}

# is_trailer_line <line> / is_closing_line <line> — classifiers for the splice.
is_trailer_line() { printf '%s' "${1:-}" | grep -qiE '^[[:space:]]*co-authored-by:'; }
is_closing_line() { printf '%s' "${1:-}" | grep -qiE '^[[:space:]]*(closes?|closed|fixes?|fixed|resolves?|resolved|refs?)([^[:alnum:]_]|$)'; }

# pr_co_author_trailers <merger-login> — stdin `login<TAB>name<TAB>email` rows (the commits
# endpoint shape, see merge_pr), stdout one `Co-authored-by:` line per distinct author
# except the merger. Skips rows with empty name/email and emails already trailered in
# $BODY (case-insensitive); dedupes by lowercase email keeping first occurrence. An empty
# merger login credits everyone — redundant trailers are harmless, missing ones are not.
pr_co_author_trailers() {
  local merger_key login name email key seen existing tsv row
  merger_key=$(printf '%s' "${1:-}" | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')
  existing=$(printf '%s' "$BODY" | existing_trailer_emails)
  seen=""
  tsv=$(cat)
  # Split on tabs by hand: `read` drops a leading empty field, which would shift an
  # unlinked author's name/email left and silently skip them.
  while IFS= read -r row || [[ -n "$row" ]]; do
    [[ -n "$row" ]] || continue
    login=""
    if [[ "$row" == $'\t'* ]]; then
      row="${row#$'\t'}"
    elif [[ "$row" == *$'\t'* ]]; then
      login="${row%%$'\t'*}"
      row="${row#*$'\t'}"
    else
      continue
    fi
    if [[ "$row" == *$'\t'* ]]; then
      name="${row%%$'\t'*}"
      email="${row#*$'\t'}"
    else
      name="$row"
      email=""
    fi
    login=$(printf '%s' "$login" | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')
    name="${name#"${name%%[![:space:]]*}"}"
    name="${name%"${name##*[![:space:]]}"}"
    email=$(printf '%s' "$email" | tr -d '[:space:]')
    key=$(printf '%s' "$email" | tr '[:upper:]' '[:lower:]')
    [[ -n "$name" && -n "$email" ]] || continue
    [[ -z "$merger_key" || "$login" != "$merger_key" ]] || continue
    if list_contains "$seen" "$key"; then continue; fi
    if list_contains "$existing" "$key"; then continue; fi
    if [[ -z "$seen" ]]; then seen="$key"; else seen="${seen}"$'\n'"${key}"; fi
    printf 'Co-authored-by: %s <%s>\n' "$name" "$email"
  done <<<"$tsv" || true
}

# insert_trailers — stdin new trailer lines, $BODY in, spliced message on stdout. Existing
# body trailers are deduped (first occurrence wins) and moved with the new ones ahead of
# the first Closes/Fixes/Resolves/Refs line (appended at end when none). Prints $BODY
# byte-identical when there is nothing to add, dedupe, or move.
insert_trailers() {
  local new_text line key seen existing_block stripped
  local dupes=0 below=0 closing_seen=0
  new_text=$(cat)
  seen=""
  existing_block=""
  stripped=""
  while IFS= read -r line || [[ -n "$line" ]]; do
    if is_trailer_line "$line"; then
      key=$(trailer_email_key "$line")
      if [[ -n "$key" ]]; then
        if list_contains "$seen" "$key"; then
          dupes=1
        else
          if [[ -z "$seen" ]]; then seen="$key"; else seen="${seen}"$'\n'"${key}"; fi
          if [[ -z "$existing_block" ]]; then existing_block="$line"; else existing_block="${existing_block}"$'\n'"${line}"; fi
        fi
        if ((closing_seen)); then below=1; fi
        continue
      fi
    fi
    if ((closing_seen == 0)) && is_closing_line "$line"; then closing_seen=1; fi
    if [[ -z "$stripped" ]]; then stripped="$line"; else stripped="${stripped}"$'\n'"${line}"; fi
  done <<<"$BODY" || true
  if [[ -z "$new_text" && $dupes -eq 0 && $below -eq 0 ]]; then
    printf '%s' "$BODY"
    return 0
  fi
  local before after found all out
  before=""
  after=""
  found=0
  while IFS= read -r line || [[ -n "$line" ]]; do
    if ((found == 0)) && is_closing_line "$line"; then
      found=1
      if [[ -z "$after" ]]; then after="$line"; else after="${after}"$'\n'"${line}"; fi
    elif ((found == 0)); then
      if [[ -z "$before" ]]; then before="$line"; else before="${before}"$'\n'"${line}"; fi
    else
      after="${after}"$'\n'"${line}"
    fi
  done <<<"$stripped" || true
  all="$existing_block"
  if [[ -n "$new_text" ]]; then
    if [[ -z "$all" ]]; then all="$new_text"; else all="${all}"$'\n'"${new_text}"; fi
  fi
  while [[ "$before" == *$'\n' ]]; do before="${before%$'\n'}"; done
  while [[ "$after" == *$'\n' ]]; do after="${after%$'\n'}"; done
  while [[ "$after" == $'\n'* ]]; do after="${after#$'\n'}"; done
  out="$before"
  if [[ -n "$all" ]]; then
    if [[ -n "$out" ]]; then out="${out}"$'\n\n'"${all}"; else out="$all"; fi
    if [[ -n "$after" ]]; then out="${out}"$'\n\n'"${after}"; fi
  else
    if [[ -n "$after" ]]; then
      if [[ -n "$out" ]]; then out="${out}"$'\n'"${after}"; else out="$after"; fi
    fi
  fi
  if [[ "$BODY" == *$'\n' ]]; then out="${out}"$'\n'; fi
  printf '%s' "$out"
}

# refuse_raw_token — stdin message; refuses a body still holding the template token.
refuse_raw_token() {
  local text
  text=$(cat)
  if printf '%s' "$text" | grep -qF -- "$CODE_AUTHORS_TOKEN"; then
    echo "refusing squash message: raw $CODE_AUTHORS_TOKEN token still present" >&2
    echo "remediation: replace the token with Co-authored-by lines for outside contributors (or delete the block), then re-run" >&2
    return 1
  fi
}

# refuse_long_lines — stdin message; refuses lines over SQUASH_LINE_MAX with numbers.
refuse_long_lines() {
  local text line bad lineno
  text=$(cat)
  bad=""
  lineno=0
  while IFS= read -r line || [[ -n "$line" ]]; do
    lineno=$((lineno + 1))
    if ((${#line} > SQUASH_LINE_MAX)); then
      if [[ -z "$bad" ]]; then bad="$lineno"; else bad="${bad} ${lineno}"; fi
    fi
  done <<<"$text" || true
  if [[ -n "$bad" ]]; then
    echo "refusing squash message: lines exceed $SQUASH_LINE_MAX chars: $bad" >&2
    echo "remediation: wrap the listed lines, then re-run" >&2
    return 1
  fi
}

# finalize_squash_message <msg> — token gate, trailer splice, length gate. stdout the
# message, stderr the announcement of appended trailers. Returns 1 on any refusal.
finalize_squash_message() {
  local msg merger tsv new final old_body
  msg="${1:-}"
  if ! printf '%s' "$msg" | refuse_raw_token; then
    return 1
  fi
  merger=$(gh api user --jq .login 2>/dev/null || echo "")
  tsv=$(gh api "repos/$REPO/pulls/$NUM/commits" --jq '.[] | [(.author.login // ""), (.commit.author.name // ""), (.commit.author.email // "")] | @tsv' 2>/dev/null || echo "")
  old_body="$BODY"
  BODY="$msg"
  new=$(printf '%s' "$tsv" | pr_co_author_trailers "$merger")
  BODY="$msg"
  final=$(printf '%s' "$new" | insert_trailers)
  BODY="$old_body"
  if ! printf '%s' "$final" | refuse_long_lines; then
    return 1
  fi
  if [[ -n "$new" ]]; then
    echo "appended trailers:" >&2
    printf '%s\n' "$new" >&2
  fi
  printf '%s' "$final"
}

# check_trailers — --check dry run: print the trailers a merge would append (no PR created).
check_trailers() {
  local merger tsv found trailers
  found=$(gh api "repos/$REPO/pulls?head=${REPO%%/*}:$HEAD_REF&state=open" --jq '.[0].number' 2>/dev/null || echo "")
  if [[ -z "$found" || "$found" == "null" ]]; then
    echo "no open PR for head $HEAD_REF" >&2
    return 2
  fi
  NUM="$found"
  BODY=$(gh api "repos/$REPO/pulls/$NUM" --jq '.body // ""' 2>/dev/null || echo "")
  merger=$(gh api user --jq .login 2>/dev/null || echo "")
  tsv=$(gh api "repos/$REPO/pulls/$NUM/commits" --jq '.[] | [(.author.login // ""), (.commit.author.name // ""), (.commit.author.email // "")] | @tsv' 2>/dev/null || echo "")
  trailers=$(printf '%s' "$tsv" | pr_co_author_trailers "$merger")
  if [[ -n "$trailers" ]]; then
    printf '%s\n' "$trailers"
  else
    echo "no co-author trailers would be appended for #$NUM" >&2
  fi
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
    # Explicit commit_message disables GitHub's auto-attribution, so the trailers are
    # rebuilt here; any refusal aborts before the merge API call.
    if ! msg=$(finalize_squash_message "$msg"); then
      return 1
    fi
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
  if [[ $CHECK -eq 1 ]]; then
    check_trailers
    exit 0
  fi
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
