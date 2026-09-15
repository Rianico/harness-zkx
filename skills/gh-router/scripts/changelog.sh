#!/usr/bin/env bash
# changelog.sh — rebuild the Unreleased block instead of hand-merging it. Dry-run by default.
#
#   changelog.sh sync [--apply] [--base main] [--changelog CHANGELOG.md]
#
# Why: the block is generated, but the file around it collects formatter churn. Rebuilding from
# the base branch and regenerating the block keeps a commit to the entries that actually changed —
# `git add CHANGELOG.md` after a formatter pass sweeps hundreds of lines into unrelated commits.
#
# Usage: changelog.sh sync [--apply] [--base B] [--changelog FILE]
# Exit: 0 ok | 1 diff too large, refused | 2 usage | 3 missing tool
# Requires: Bash >=4.4, git, python3

set -Eeuo pipefail
shopt -s inherit_errexit 2>/dev/null || true

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LIB_DIR="$(cd "$SCRIPT_DIR/../lib" && pwd)"
# shellcheck source=../lib/log.sh
source "$LIB_DIR/log.sh"
# shellcheck source=../lib/repo.sh
source "$LIB_DIR/repo.sh"
# log.sh sets -uo pipefail; re-assert strictness after sourcing.
set -Eeuo pipefail
IFS=$'\n\t'

# A truthful sync touches the Unreleased block only; more means the base file was not used.
MAX_CHANGED_LINES=40
COMMIT_MESSAGE="chore: sync changelog unreleased section"

command="${1:-}"
case "$command" in
-h | --help)
  sed -n '2,12p' "$0" | sed 's/^# \?//'
  exit 0
  ;;
esac
[[ "$command" == "sync" ]] || fail "usage: changelog.sh sync [--apply] [--base B] [--changelog FILE]" 2
shift || true

APPLY=0
BASE=""
CHANGELOG="CHANGELOG.md"
while [[ $# -gt 0 ]]; do
  case "$1" in
  --apply)
    APPLY=1
    shift
    ;;
  --base)
    BASE="$2"
    shift 2
    ;;
  --changelog)
    CHANGELOG="$2"
    shift 2
    ;;
  *) shift ;;
  esac
done

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || fail "not a git repository" 2
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT" || exit 2
command -v python3 >/dev/null 2>&1 || fail "python3 not found" 3
[[ -f scripts/changelog-unreleased.py ]] || fail "no scripts/changelog-unreleased.py in $ROOT" 3

if [[ -z "$BASE" ]]; then
  BASE="$(default_branch || true)"
  BASE="${BASE:-main}"
fi
if ! git rev-parse --verify -q "origin/$BASE" >/dev/null; then
  git fetch -q origin "$BASE" 2>/dev/null || fail "unknown base branch: $BASE" 2
fi

base_file="$(mktemp)"
rebuilt="$(mktemp)"
trap 'rm -f -- "$base_file" "$rebuilt"' EXIT
git show "origin/$BASE:$CHANGELOG" >"$base_file" 2>/dev/null || fail "$CHANGELOG does not exist on origin/$BASE" 1

# Rebuild = base file + regenerated block, so formatting drift cannot ride along.
cp "$base_file" "$rebuilt"
python3 scripts/changelog-unreleased.py update --changelog "$rebuilt" >/dev/null

added="$(diff "$CHANGELOG" "$rebuilt" 2>/dev/null | grep -c '^>' || true)"
removed="$(diff "$CHANGELOG" "$rebuilt" 2>/dev/null | grep -c '^<' || true)"
changed=$((${added:-0} + ${removed:-0}))
vs_head="$(git diff --numstat HEAD -- "$CHANGELOG" | awk '{print $1 + $2}')"

if [[ "$changed" -eq 0 ]]; then
  ok "$CHANGELOG already matches origin/$BASE + regenerated block"
  exit 0
fi
step "$CHANGELOG: rebuild would change $changed lines (+${added:-0}/-${removed:-0}) vs working file"

if [[ "$changed" -gt "$MAX_CHANGED_LINES" ]]; then
  fail "$CHANGELOG: refusing — $changed lines changed (> $MAX_CHANGED_LINES), formatter churn rather than a sync" 1
fi

if [[ "$APPLY" != "1" ]]; then
  info "dry run — pass --apply to rebuild, stage and commit"
  exit 0
fi

cp "$rebuilt" "$CHANGELOG"
git add -- "$CHANGELOG"
if [[ -n "$vs_head" && "$vs_head" -eq 0 ]]; then
  ok "$CHANGELOG rebuilt; nothing staged beyond HEAD"
  exit 0
fi
git commit -q -m "$COMMIT_MESSAGE" -m "Rebuilt from origin/$BASE plus the regenerated Unreleased block." \
  -m "Co-authored-by: deepseek-v4.1-flash <noreply@ai>"
ok "staged and committed: $COMMIT_MESSAGE (+${added:-0}/-${removed:-0})"
