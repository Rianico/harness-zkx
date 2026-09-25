#!/usr/bin/env bash
# refine.sh — take over and refine a contributor's PR (Flow A or B).
# Usage: scripts/refine.sh observe NUM | checkout NUM | lint-body --body-file FILE
#   observe  : deterministic gate — prints maintainerCanModify, head/base repos, and the
#              resulting flow (A = push onto their branch, B = superseding PR). No judgment.
#              Same-repo heads always take Flow A: maintainerCanModify is false for
#              in-repo branches (it only means anything for forks), and you already
#              hold the push access pr-land demands.
#   checkout : check out the contributor's head intact (never rewrite their history).
#   lint-body: refuse a body still holding the raw CODE_AUTHORS token (line-length
#              limit dropped per commit #135) — same gates pr-land enforces.
# Seam: refine pushes, land merges — hand the branch and body to pr-land/scripts/pr.sh.
# Exit: 0 ok | 1 gate refused or gh failed | 2 usage.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$(cd "$SCRIPT_DIR/../../../lib" && pwd)"
# shellcheck source=../../../lib/repo.sh
source "$LIB_DIR/repo.sh"

CODE_AUTHORS_TOKEN="CODE_AUTHORS"

refuse_raw_token() {
  local text
  text=$(cat)
  if printf '%s' "$text" | awk '
    {
      line = $0
      while (match(line, /<!--|-->/)) {
        before = substr(line, 1, RSTART - 1)
        tok = substr(line, RSTART, RLENGTH)
        if (incomment && index(before, "CODE_AUTHORS")) found = 1
        if (tok == "<!--") incomment = 1
        else incomment = 0
        line = substr(line, RSTART + RLENGTH)
      }
      if (incomment && index(line, "CODE_AUTHORS")) found = 1
    }
    END { exit !found }'; then
    echo "refusing squash message: raw $CODE_AUTHORS_TOKEN token still present" >&2
    echo "remediation: replace the token with Co-authored-by lines for outside contributors (or delete the block), then re-run" >&2
    return 1
  fi
}

usage() { sed -n '2,9p' "$0"; }

observe_pr() {
  local num="${1:-}" payload can_modify head_repo base_repo repo
  if [[ ! "$num" =~ ^[0-9]+$ ]]; then
    echo "usage: refine.sh observe NUM" >&2
    return 2
  fi
  if ! repo=$(repo_slug); then
    echo "observe: cannot resolve repo slug" >&2
    return 1
  fi
  # REST: `gh pr view --json` has no baseRepository field. An empty head repo
  # (deleted fork) keeps Flow B.
  payload=$(gh api "repos/$repo/pulls/$num" \
    --jq '[.maintainer_can_modify, (.head.repo.full_name // ""), .base.repo.full_name] | @tsv' 2>/dev/null || echo "")
  if [[ -z "$payload" ]]; then
    echo "observe: gh api repos/$repo/pulls/$num failed" >&2
    return 1
  fi
  # Split by hand: `read` drops leading empty fields, which would shift a null
  # head repo (deleted fork) into the wrong column on display.
  if [[ "$payload" != *$'\t'*$'\t'* ]]; then
    echo "observe: unexpected response shape" >&2
    return 1
  fi
  can_modify="${payload%%$'\t'*}"
  head_repo="${payload#*$'\t'}"
  base_repo="${head_repo#*$'\t'}"
  head_repo="${head_repo%%$'\t'*}"
  echo "maintainerCanModify=$can_modify"
  echo "headRepo=$head_repo"
  echo "baseRepo=$base_repo"
  if [[ "$can_modify" == "true" || (-n "$head_repo" && "$head_repo" == "$base_repo") ]]; then
    echo "flow=A (push refinements onto their branch, merge their PR via pr-land)"
  else
    echo "flow=B (merge their head intact into your branch, open a superseding PR)"
  fi
}

checkout_pr() {
  local num="${1:-}"
  if [[ ! "$num" =~ ^[0-9]+$ ]]; then
    echo "usage: refine.sh checkout NUM" >&2
    return 2
  fi
  gh pr checkout "$num"
  # Preservation rule: their history is read-only. Merge it, never rebase or amend it.
  echo "checked out #$num intact — merge, do not rewrite; supersede via a new PR" >&2
}

lint_body() {
  local file=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
    --body-file)
      file="$2"
      shift 2
      ;;
    -h | --help)
      usage
      return 0
      ;;
    *)
      echo "unknown arg: $1" >&2
      return 2
      ;;
    esac
  done
  if [[ -z "$file" || ! -f "$file" || ! -r "$file" ]]; then
    echo "body file not found or not readable: $file" >&2
    return 2
  fi
  BODY=$(cat -- "$file")
  local ok=0
  if ! printf '%s' "$BODY" | refuse_raw_token; then ok=1; fi
  if ((ok == 0)); then
    echo "body ok: no raw token"
  fi
  return "$ok"
}

main() {
  local cmd="${1:-}"
  case "$cmd" in
  observe) observe_pr "${2:-}" ;;
  checkout) checkout_pr "${2:-}" ;;
  lint-body) lint_body "${@:2}" ;;
  -h | --help) usage ;;
  *) usage >&2; return 2 ;;
  esac
}

# Sourced for tests: only define, never act.
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
