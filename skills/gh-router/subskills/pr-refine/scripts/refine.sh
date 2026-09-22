#!/usr/bin/env bash
# refine.sh — take over and refine a contributor's PR (Flow A or B).
# Usage: scripts/refine.sh observe NUM | checkout NUM | lint-body --body-file FILE
#   observe  : deterministic gate — prints maintainerCanModify, head, author, base, and the
#              resulting flow (A = push onto their branch, B = superseding PR). No judgment.
#   checkout : check out the contributor's head intact (never rewrite their history).
#   lint-body: refuse a body still holding the raw CODE_AUTHORS token or a line over
#              100 chars (commitlint body-max-line-length) — same gates pr-land enforces.
# Seam: refine pushes, land merges — hand the branch and body to pr-land/scripts/pr.sh.
# Exit: 0 ok | 1 gate refused or gh failed | 2 usage.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PR_SH="$(cd "$SCRIPT_DIR/../../pr-land/scripts" && pwd)/pr.sh"
# Attribution gates live in pr-land; this script reuses them, never re-derives them.
# shellcheck source=../../pr-land/scripts/pr.sh
source "$PR_SH"

usage() { sed -n '2,9p' "$0"; }

observe_pr() {
  local num="${1:-}" payload can_modify head_ref head_repo author base
  if [[ ! "$num" =~ ^[0-9]+$ ]]; then
    echo "usage: refine.sh observe NUM" >&2
    return 2
  fi
  payload=$(gh pr view "$num" --json maintainerCanModify,headRefName,headRepository,author,baseRefName \
    --jq '[.maintainerCanModify, .headRefName, .headRepository.nameWithOwner, .author.login, .baseRefName] | @tsv' 2>/dev/null || echo "")
  if [[ -z "$payload" ]]; then
    echo "observe: gh pr view $num failed" >&2
    return 1
  fi
  IFS=$'\t' read -r can_modify head_ref head_repo author base <<<"$payload"
  echo "maintainerCanModify=$can_modify"
  echo "head=$head_repo:$head_ref"
  echo "author=$author"
  echo "base=$base"
  if [[ "$can_modify" == "true" ]]; then
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
  if ! printf '%s' "$BODY" | refuse_long_lines; then ok=1; fi
  if ((ok == 0)); then
    echo "body ok: no raw token, all lines <= $SQUASH_LINE_MAX"
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
