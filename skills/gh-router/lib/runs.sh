#!/usr/bin/env bash
# runs.sh — read a GitHub Actions run's failure facts.
#
# Sourced, never executed. Same contract as repo.sh: prints ONLY the value on stdout,
# returns a value or nothing instead of printing a diagnostic, installs no ERR trap and
# changes no shell option. Callers own rendering (lib/log.sh) and the exit code.
#
# Why this is its own module: both release paths (dispatch.sh and release-watch.sh) end a
# failed watch, and an operator at that moment needs the failing job › step before the log
# tail. One reader keeps both reports honest, and keeps the rule that a reporting helper
# must never exit before the diagnostics that follow it.

# run_failing_steps <repo> <run-id> [limit]
# One `job › step` line per failing step; a failed job with no failed step prints its name.
# Bounded to [limit] lines (default 5). Prints nothing when gh cannot answer, and always
# exits 0, so a diagnostics call can never abort the failure path it exists to report.
run_failing_steps() {
  local repo="${1:-}" run_id="${2:-}" limit="${3:-5}"
  [[ -n "$repo" && -n "$run_id" ]] || return 0
  gh api "repos/$repo/actions/runs/$run_id/jobs" 2>/dev/null |
    HARNESS_STEP_LIMIT="$limit" python3 -c '
import json, os, sys

limit = int(os.environ.get("HARNESS_STEP_LIMIT", "5"))
try:
    jobs = json.load(sys.stdin).get("jobs") or []
except Exception:
    sys.exit(0)

failed = ("failure", "timed_out", "cancelled")
bad = []
for job in jobs:
    name = job.get("name") or "?"
    steps = [s for s in (job.get("steps") or []) if (s.get("conclusion") or "") in failed]
    if steps:
        bad.extend("{} \u203a {}".format(name, s.get("name") or "?") for s in steps)
    elif (job.get("conclusion") or "") in failed:
        bad.append(name)
for line in bad[:limit]:
    print(line)
' || true
}

# run_log_tail <repo> <run-id> [lines]
# Bounded tail (default 120 lines) of the failing log, never the whole trace. Falls back to
# the run summary when GitHub has no failed-step log to return. Prints nothing on failure;
# always exits 0.
run_log_tail() {
  local repo="${1:-}" run_id="${2:-}" lines="${3:-120}" tmp rc=0
  [[ -n "$repo" && -n "$run_id" ]] || return 0
  tmp="$(mktemp)"
  gh run view "$run_id" --repo "$repo" --log-failed >"$tmp" 2>&1 || rc=$?
  if [[ $rc -ne 0 || ! -s "$tmp" ]]; then
    gh run view "$run_id" --repo "$repo" >"$tmp" 2>&1 || true
  fi
  tail -n "$lines" "$tmp" 2>/dev/null || true
  rm -f "$tmp"
}
