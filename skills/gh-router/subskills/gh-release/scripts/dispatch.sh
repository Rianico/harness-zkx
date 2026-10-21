#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LIB_DIR="$(cd "$SCRIPT_DIR/../../../lib" && pwd)"
# shellcheck source=../../../lib/log.sh
source "$LIB_DIR/log.sh"
# shellcheck source=../../../lib/repo.sh
source "$LIB_DIR/repo.sh"
# shellcheck source=../../../lib/runs.sh
source "$LIB_DIR/runs.sh"

DRY="false"
# Bounded log tail for a failed run: enough to name the cause, small enough to stay readable.
LOG_TAIL_LINES=120
if [[ "${1:-}" == "--dry-run" ]]; then DRY="true"; fi

# fetch token once
GITHUB_TOKEN="$(gh auth token 2>/dev/null || true)"
if [[ -z "$GITHUB_TOKEN" ]]; then
  phase_fail 3 "gh auth token unavailable — run: gh auth login"
  exit 1
fi
export GITHUB_TOKEN

NEXT_VER=""

# Run semantic-release --dry-run but print ONLY the concise summary (version +
# release-note body). The full plugin trace is discarded — it is unrelated noise
# that would otherwise flood the context window. Full log available on demand via
# the hint printed by `preview`.
# condensed_notes <trace> — the curated release-note lines from a semantic-release dry-run.
#
# The trace logs every analyzed commit message with its body (`Analyzing commit: …`), so a
# bare heading filter reprinted the commit body's own `## Summary`/`## Root Cause` headings
# above the real notes (#284). Prefer the block semantic-release prints after its
# `Release note for version` marker; a trace without that marker (older releases) falls back
# to dropping the `Analyzing commit:` blocks, the only place a commit body appears.
condensed_notes() {
  local trace="$1" body
  if printf '%s\n' "$trace" | grep -qE '^\[[^]]*\] \[semantic-release\].*Release note for version '; then
    body=$(printf '%s\n' "$trace" | awk '
      /^\[[^]]*\] \[semantic-release\].*Release note for version / { found = 1; next }
      found && /^\[[^]]*\] \[semantic-release\]/ { exit }
      found { print }
    ')
  else
    body=$(printf '%s\n' "$trace" | awk '
      /Analyzing commit:/ { skipping = 1; next }
      skipping && /^\[[^]]*\] \[semantic-release\]/ { skipping = 0 }
      !skipping { print }
    ')
  fi
  printf '%s\n' "$body" | grep -E "^(##|###) |^    \* |^  \* |^\* " | head -n 50 || true
  return 0
}

preview() {
  local tmp out _pm_exec sr_exit rc=0
  tmp=$(mktemp)
  # Detect package manager for semantic-release (npm vs pnpm)
  _pm_exec="npx --silent"
  if [[ -f pnpm-lock.yaml ]]; then
    _pm_exec="pnpm exec"
  elif grep -q '"packageManager"[[:space:]]*:[[:space:]]*"pnpm' package.json 2>/dev/null; then
    _pm_exec="pnpm exec"
  elif [[ -f pnpm-workspace.yaml ]]; then
    _pm_exec="pnpm exec"
  fi
  set +e
  GITHUB_TOKEN="$GITHUB_TOKEN" $_pm_exec semantic-release --dry-run >"$tmp" 2>&1
  sr_exit=$?
  set -e
  out=$(cat "$tmp")
  rm -f "$tmp"
  NEXT_VER=$(echo "$out" | grep -oE "The next release version is [0-9][^ ]*" | tail -n1 | awk '{print $NF}' || true)
  if [[ ${sr_exit} -ne 0 ]]; then
    # semantic-release itself failed (e.g. network/SSL error during git fetch) —
    # surface the real error instead of misreporting it as "no new version".
    warn "semantic-release dry-run failed (exit ${sr_exit})"
    echo "${out}" | tail -n 20 || true
    rc=1
  elif [[ -n "$NEXT_VER" ]]; then
    ok "next version: v$NEXT_VER"
    # condensed release-note body: section headers and bullet lines, selected from the
    # release notes only so a commit body cannot masquerade as release content.
    condensed_notes "$out"
  else
    warn "no new version — nothing to release"
    dim "commits since last tag do not trigger a release (need feat/fix/! or BREAKING CHANGE)"
  fi
  # Provide full-trace hint matching the detected package manager
  if [[ "${_pm_exec}" == "pnpm exec" ]]; then
    dim "full trace: GITHUB_TOKEN=\$(gh auth token) pnpm exec semantic-release --dry-run"
  else
    dim "full trace: GITHUB_TOKEN=\$(gh auth token) npx semantic-release --dry-run"
  fi
  return "${rc}"
}

if [[ "$DRY" == "true" ]]; then
  phase 3 3 "Preview — dry-run (no publish)"
  info "running semantic-release --dry-run…"
  preview
  preview_rc=$?
  if [[ ${preview_rc} -ne 0 ]]; then
    phase_fail 3 "semantic-release dry-run failed"
    exit 1
  fi
  phase_ok 3 "dry-run complete"
  exit 0
fi

# non-dry-run: preview + prompt + dispatch + watch
phase 3 3 "Preview → Dispatch → Watch"

info "running semantic-release --dry-run (preview)…"
preview
preview_rc=$?
if [[ ${preview_rc} -ne 0 ]]; then
  phase_fail 3 "semantic-release dry-run failed — holding (no dispatch on unknown version)"
  exit 1
fi

if [[ -z "$NEXT_VER" ]]; then
  warn "no new version detected — dispatch will be a no-op (GitHub will receive event but semantic-release will skip)"
  read -r -p "a: dispatch anyway   b: hold > " ans
  if [[ "$ans" != "a" ]]; then
    warn "hold — not dispatched"
    phase_ok 3 "aborted by user"
    exit 0
  fi
else
  echo ""
  printf "%s Publish v%s ? %s\n" "${_C_BOLD}" "$NEXT_VER" "$_C_RESET"
  read -r -p "a: dispatch (publish)   b: hold > " ans
  if [[ "$ans" != "a" ]]; then
    warn "hold — not dispatched"
    phase_ok 3 "aborted by user"
    exit 0
  fi
fi

# Resolve the release repo from this checkout's push remote (never `gh repo view`,
# which can point at an upstream/fork and dispatch a release at the wrong project).
if ! OWNER_REPO=$(repo_slug); then
  phase_fail 3 "cannot resolve release repo slug (no GitHub remote for branch/origin)"
  exit 1
fi

# capture latest run id before dispatch so we can detect the new one
BEFORE_ID=$(gh run list --repo "$OWNER_REPO" --workflow release.yml --event repository_dispatch --limit 1 --json databaseId --jq '.[0].databaseId // empty' 2>/dev/null || echo "")
info "dispatching semantic-release to ${OWNER_REPO}…"
if ! gh api "repos/${OWNER_REPO}/dispatches" -f event_type=semantic-release >/dev/null 2>&1; then
  phase_fail 3 "gh api dispatch failed for ${OWNER_REPO}"
  exit 1
fi
ok "dispatched ${OWNER_REPO}"
dim "Actions: https://github.com/${OWNER_REPO}/actions"

# --- watch dispatched workflow until completion (quiet poll, no TUI frames) ---
info "waiting for workflow run to appear…"
RUN_ID=""
for _ in $(seq 1 30); do
  sleep 2
  CANDIDATE=$(gh run list --repo "$OWNER_REPO" --workflow release.yml --event repository_dispatch --limit 5 --json databaseId --jq '.[0].databaseId // empty' 2>/dev/null || true)
  # fallback to workflow name if file filter yields nothing (e.g. renamed workflow file)
  if [[ -z "$CANDIDATE" ]]; then
    CANDIDATE=$(gh run list --repo "$OWNER_REPO" --workflow "Verify and Release" --event repository_dispatch --limit 5 --json databaseId --jq '.[0].databaseId // empty' 2>/dev/null || true)
  fi
  if [[ -n "$CANDIDATE" && "$CANDIDATE" != "$BEFORE_ID" ]]; then
    RUN_ID="$CANDIDATE"
    break
  fi
done

if [[ -z "$RUN_ID" ]]; then
  warn "dispatched but no workflow run appeared within ~60s"
  dim "check manually: https://github.com/${OWNER_REPO}/actions/workflows/release.yml"
  dim "or: gh run list --repo ${OWNER_REPO} --workflow release.yml --event repository_dispatch --limit 5"
  phase_ok 3 "dispatched (watch skipped — run not yet visible)"
  exit 0
fi

info "watching run ${RUN_ID} — https://github.com/${OWNER_REPO}/actions/runs/${RUN_ID} (quiet poll, no per-job output)"
# Poll status quietly; emit nothing until completion to keep the context window clean.
RC=1
for _ in $(seq 1 120); do
  ST=$(gh run view "$RUN_ID" --repo "$OWNER_REPO" --json status,conclusion --jq '.status + " " + (.conclusion // "")' 2>/dev/null || true)
  STATUS="${ST%% *}"
  CONCLUSION="${ST#* }"
  if [[ "$STATUS" == "completed" ]]; then
    if [[ "$CONCLUSION" == "success" ]]; then
      ok "workflow completed: success"
      RC=0
    else
      RC=1
    fi
    break
  fi
  sleep 5
done

echo ""
if [[ $RC -eq 0 ]]; then
  ok "release workflow succeeded — run ${RUN_ID}"
  git fetch --tags --quiet 2>/dev/null || true
  dim "tags: $(git tag --sort=-v:refname | head -n 5 | tr '\n' ' ' 2>/dev/null || echo n/a)"
  if [[ -f CHANGELOG.md ]]; then
    dim "CHANGELOG head:"
    head -n 12 CHANGELOG.md | sed 's/^/  /' || true
  fi
  dim "run: https://github.com/${OWNER_REPO}/actions/runs/${RUN_ID}"
  phase_ok 3 "released v${NEXT_VER:-unknown} — workflow ${RUN_ID} passed"
else
  _conclusion=$(gh run view "$RUN_ID" --repo "$OWNER_REPO" --json conclusion --jq '.conclusion // "failed"' 2>/dev/null || echo "failed")
  phase_fail 3 "release workflow ${_conclusion:-failed} — run ${RUN_ID}"
  # Diagnostics before the exit, never after it: print the failing job › step and a
  # bounded log tail so the operator does not have to re-derive either by hand.
  _steps=$(run_failing_steps "$OWNER_REPO" "$RUN_ID")
  if [[ -n "$_steps" ]]; then
    while IFS= read -r _step_line; do fail_line "$_step_line"; done <<<"$_steps"
  else
    warn "no failing job or step reported for run ${RUN_ID}"
  fi
  warn "log tail (last ${LOG_TAIL_LINES} lines):"
  run_log_tail "$OWNER_REPO" "$RUN_ID" "$LOG_TAIL_LINES" >&2 || true
  dim "view: gh run view ${RUN_ID} --repo ${OWNER_REPO} --log-failed"
  dim "web:  https://github.com/${OWNER_REPO}/actions/runs/${RUN_ID}"
  exit 1
fi
