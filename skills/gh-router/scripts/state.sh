#!/usr/bin/env bash
# state.sh — one-call orientation. Read-only.
#
# Answers the four questions every turn starts with, one line each:
#   branch  <head> → <base> (ahead N, behind M)
#   pr      #<num> <mergeable>/<mergeState> checks <ok>/<total>
#   guard   in sync | stale (N lines) | no changelog script
#   main    <sha> <subject> (<tag>)
#
# Usage: state.sh [--base <branch>] [--head <branch>] [--json]
# Exit: 0 ok | 2 not a git repo | 3 gh unavailable

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LIB_DIR="$(cd "$SCRIPT_DIR/../lib" && pwd)"
# shellcheck source=../lib/log.sh
source "$LIB_DIR/log.sh"
# shellcheck source=../lib/repo.sh
source "$LIB_DIR/repo.sh"

BASE=""
HEAD_REF=""
JSON=0
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
  --json)
    JSON=1
    shift
    ;;
  -h | --help)
    sed -n '2,12p' "$0" | sed 's/^# \?//'
    exit 0
    ;;
  *) shift ;;
  esac
done

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || fail "not a git repository" 2
command -v gh >/dev/null 2>&1 || fail "gh CLI not found" 3

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT" || exit 2

[[ -n "$HEAD_REF" ]] || HEAD_REF="$(git rev-parse --abbrev-ref HEAD)"
[[ -n "$BASE" ]] || BASE="$(default_branch || echo main)"

git fetch -q origin "$BASE" 2>/dev/null || true

# --- branch divergence
ahead=0
behind=0
if git rev-parse --verify -q "origin/$BASE" >/dev/null; then
  read -r behind ahead <<<"$(git rev-list --left-right --count "origin/$BASE...$HEAD_REF" 2>/dev/null || echo "0 0")"
fi

# --- PR state + checks
pr_line="-"
checks_ok=0
checks_total=0
pr_json="$(gh pr view "$HEAD_REF" --json number,mergeable,mergeStateStatus,statusCheckRollup 2>/dev/null || true)"
if [[ -n "$pr_json" ]]; then
  IFS=$'\t' read -r pr_num pr_merge pr_state checks_ok checks_total <<<"$(
    printf '%s' "$pr_json" | python3 -c '
import json,sys
d=json.load(sys.stdin)
roll=d.get("statusCheckRollup") or []
ok=sum(1 for c in roll if (c.get("conclusion") or "").upper() in ("SUCCESS","NEUTRAL","SKIPPED"))
num=d.get("number","?")
m=d.get("mergeable") or "?"
s=d.get("mergeStateStatus") or "?"
print(f"{num}\t{m}\t{s}\t{ok}\t{len(roll)}")
'
  )"
  pr_line="#$pr_num $pr_merge/$pr_state checks $checks_ok/$checks_total"
fi

# --- changelog guard verdict
guard_line="no changelog script"
if [[ -f "$ROOT/scripts/changelog-gate.py" ]] && [[ -f "$ROOT/CHANGELOG.md" ]]; then
  if python3 "$ROOT/scripts/changelog-gate.py" ledger >/dev/null 2>&1; then
    guard_line="ledger ok"
  else
    guard_line="ledger has findings"
  fi
fi

# --- base tip
main_sha="$(git rev-parse --short "origin/$BASE" 2>/dev/null || echo '?')"
main_subject="$(git log -1 --pretty=%s "origin/$BASE" 2>/dev/null || echo '?')"
main_tag="$(git describe --tags --abbrev=0 "origin/$BASE" 2>/dev/null || echo '-')"

if [[ "$JSON" == "1" ]]; then
  python3 - "$HEAD_REF" "$BASE" "$ahead" "$behind" "$pr_line" "$guard_line" "$main_sha" "$main_subject" "$main_tag" <<'PY'
import json, sys
head, base, ahead, behind, pr, guard, sha, subject, tag = sys.argv[1:10]
print(json.dumps({
    "head": head, "base": base, "ahead": int(ahead), "behind": int(behind),
    "pr": pr, "guard": guard, "base_tip": {"sha": sha, "subject": subject, "tag": tag},
}, indent=2))
PY
  exit 0
fi

printf '%s\n' "branch  $HEAD_REF → $BASE (ahead $ahead, behind $behind)"
printf '%s\n' "pr      $pr_line"
printf '%s\n' "guard   $guard_line"
printf '%s\n' "main    $main_sha $main_subject ($main_tag)"
