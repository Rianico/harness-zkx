#!/usr/bin/env bash
# ci.sh — CI diagnostics without hand-rolled gh plumbing.
#
#   ci.sh runs [--branch B] [--limit N]   last N runs, one line each + slowest steps
#   ci.sh why <run-id>                    failed jobs/steps + tail of the failing log
#   ci.sh watch <run-id>                  quiet poll → one-line verdict
#
# Usage: ci.sh <runs|why|watch> [args]
# Exit: 0 ok | 1 failure | 2 usage | 3 gh unavailable
# Requires: Bash >=4.4, gh, python3

set -Eeuo pipefail
shopt -s inherit_errexit 2>/dev/null || true

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../subskills/gh-release/scripts/_common.sh
source "$SCRIPT_DIR/../subskills/gh-release/scripts/_common.sh"
# _common.sh resets options; re-assert strictness after it.
set -Eeuo pipefail
IFS=$'\n\t'

command -v gh >/dev/null 2>&1 || fail "gh CLI not found" 3
command -v python3 >/dev/null 2>&1 || fail "python3 not found" 3

command="${1:-}"
case "$command" in
  -h | --help)
    sed -n '2,11p' "$0" | sed 's/^# \?//'
    exit 0
    ;;
esac
[[ -n "$command" ]] || fail "usage: ci.sh <runs|why|watch> [args]" 2
shift || true

REPO="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"

# ---------------------------------------------------------------- runs

runs() {
  local branch="" limit=5
  while [[ $# -gt 0 ]]; do
    case "$1" in
    --branch)
      branch="$2"
      shift 2
      ;;
    --limit)
      limit="$2"
      shift 2
      ;;
    *) shift ;;
    esac
  done

  local args=(--limit "$limit" --json databaseId,name,status,conclusion,headBranch)
  [[ -n "$branch" ]] && args+=(--branch "$branch")
  local runs_json
  runs_json="$(gh run list "${args[@]}")"

  local rows
  rows="$(printf '%s' "$runs_json" | python3 -c 'import json,sys
for r in json.load(sys.stdin):
    print(str(r["databaseId"]) + "\t" + str(r["name"]) + "\t" + (r.get("conclusion") or r.get("status")))')"
  [[ -n "$rows" ]] || {
    warn "no runs found"
    return 0
  }

  local id
  while IFS=$'\t' read -r rid rname rconcl; do
    [[ -n "$rid" ]] || continue
    gh api "repos/$REPO/actions/runs/$rid/jobs" | python3 -c '
import json,sys
from datetime import datetime
d=json.load(sys.stdin)
jobs=d.get("jobs") or []
concl={j.get("conclusion") or j.get("status") for j in jobs}
state="ok" if concl and concl <= {"success","skipped","neutral"} else (sorted(concl)[0] if concl else "?")
dur=0
steps=[]
for j in jobs:
    for s in j.get("steps") or []:
        a,b=s.get("started_at"),s.get("completed_at")
        if not a or not b: continue
        sec=(datetime.fromisoformat(b.replace("Z","+00:00"))-datetime.fromisoformat(a.replace("Z","+00:00"))).seconds
        dur+=sec
        if sec >= 1: steps.append((sec,s["name"]))
steps.sort(reverse=True)
top=" ".join(f"{n}={s}s" for s,n in steps[:4])
print(f"#{sys.argv[1]} {sys.argv[2]} {sys.argv[3]} {dur}s | {top}")
' "$rid" "$rname" "$rconcl"
  done <<<"$rows"
}

# ---------------------------------------------------------------- why

why() {
  local run_id="${1:-}"
  [[ -n "$run_id" ]] || fail "usage: ci.sh why <run-id>" 2

  gh api "repos/$REPO/actions/runs/$run_id/jobs" | python3 -c '
import json,sys
d=json.load(sys.stdin)
bad=[]
for j in d.get("jobs") or []:
    for s in j.get("steps") or []:
        if (s.get("conclusion") or "") in ("failure","timed_out","cancelled"):
            bad.append(f"{j[\"name\"]} › {s[\"name\"]}")
print("\n".join(bad) if bad else "no failing step found")
' | while IFS= read -r line; do step "$line"; done

  local conclusion
  conclusion="$(gh run view "$run_id" --json conclusion --jq '.conclusion // "unknown"')"
  if [[ "$conclusion" != "failure" ]]; then
    ok "run $conclusion — nothing to explain"
    return 0
  fi
  info "failing log tail:"
  gh run view "$run_id" --log-failed 2>/dev/null | tail -20
  return 1
}

# ---------------------------------------------------------------- watch

watch() {
  local run_id="${1:-}"
  [[ -n "$run_id" ]] || fail "usage: ci.sh watch <run-id>" 2
  local status conclusion
  while :; do
    status="$(gh run view "$run_id" --json status --jq .status)"
    [[ "$status" == "completed" ]] && break
    sleep 10
  done
  conclusion="$(gh run view "$run_id" --json conclusion --jq .conclusion)"
  if [[ "$conclusion" == "success" ]]; then
    ok "run $run_id completed: success"
    return 0
  fi
  fail "run $run_id $conclusion" 1
}

case "$command" in
runs) runs "$@" ;;
why) why "$@" ;;
watch) watch "$@" ;;
-h | --help) sed -n '2,11p' "$0" | sed 's/^# \?//' ;;
*) fail "unknown command: $command (runs|why|watch)" 2 ;;
esac
