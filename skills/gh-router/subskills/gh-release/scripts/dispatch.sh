#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"

DRY="false"
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
preview() {
  local tmp out _pm_exec
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
  set -e
  out=$(cat "$tmp")
  rm -f "$tmp"
  NEXT_VER=$(echo "$out" | grep -oE "The next release version is [0-9][^ ]*" | tail -n1 | awk '{print $NF}' || true)
  if [[ -n "$NEXT_VER" ]]; then
    ok "next version: v$NEXT_VER"
    # condensed release-note body: version title, section headers, bullet lines
    echo "$out" | grep -E "^(##|###) |^    \* |^  \* |^\* " | head -n 50 || true
  else
    warn "no new version — nothing to release"
    dim "commits since last tag do not trigger a release (need feat/fix/! or BREAKING CHANGE)"
  fi
  # Provide full-trace hint matching the detected package manager
  if [[ "$_pm_exec" == "pnpm exec" ]]; then
    dim "full trace: GITHUB_TOKEN=\$(gh auth token) pnpm exec semantic-release --dry-run"
  else
    dim "full trace: GITHUB_TOKEN=\$(gh auth token) npx semantic-release --dry-run"
  fi
}

if [[ "$DRY" == "true" ]]; then
  phase 3 3 "Preview — dry-run (no publish)"
  info "running semantic-release --dry-run…"
  preview
  phase_ok 3 "dry-run complete"
  exit 0
fi

# non-dry-run: preview + prompt + dispatch + watch
phase 3 3 "Preview → Dispatch → Watch"

info "running semantic-release --dry-run (preview)…"
preview

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

# capture latest run id before dispatch so we can detect the new one
BEFORE_ID=$(gh run list --workflow release.yml --event repository_dispatch --limit 1 --json databaseId --jq '.[0].databaseId // empty' 2>/dev/null || echo "")
OWNER_REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || git remote get-url origin | sed -E 's/.*github.com[:\/](.*)\.git/\1/')
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
  CANDIDATE=$(gh run list --workflow release.yml --event repository_dispatch --limit 5 --json databaseId --jq '.[0].databaseId // empty' 2>/dev/null || true)
  # fallback to workflow name if file filter yields nothing (e.g. renamed workflow file)
  if [[ -z "$CANDIDATE" ]]; then
    CANDIDATE=$(gh run list --workflow "Verify and Release" --event repository_dispatch --limit 5 --json databaseId --jq '.[0].databaseId // empty' 2>/dev/null || true)
  fi
  if [[ -n "$CANDIDATE" && "$CANDIDATE" != "$BEFORE_ID" ]]; then
    RUN_ID="$CANDIDATE"
    break
  fi
done

if [[ -z "$RUN_ID" ]]; then
  warn "dispatched but no workflow run appeared within ~60s"
  dim "check manually: https://github.com/${OWNER_REPO}/actions/workflows/release.yml"
  dim "or: gh run list --workflow release.yml --event repository_dispatch --limit 5"
  phase_ok 3 "dispatched (watch skipped — run not yet visible)"
  exit 0
fi

info "watching run ${RUN_ID} — https://github.com/${OWNER_REPO}/actions/runs/${RUN_ID} (quiet poll, no per-job output)"
# Poll status quietly; emit nothing until completion to keep the context window clean.
RC=1
for _ in $(seq 1 120); do
  ST=$(gh run view "$RUN_ID" --json status,conclusion --jq '.status + " " + (.conclusion // "")' 2>/dev/null || true)
  STATUS="${ST%% *}"
  CONCLUSION="${ST#* }"
  if [[ "$STATUS" == "completed" ]]; then
    if [[ "$CONCLUSION" == "success" ]]; then
      ok "workflow completed: success"
      RC=0
    else
      fail "workflow completed: ${CONCLUSION:-failed}"
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
  _conclusion=$(gh run view "$RUN_ID" --json conclusion --jq .conclusion 2>/dev/null || echo "failed")
  phase_fail 3 "release workflow ${_conclusion} — run ${RUN_ID}"
  warn "fetching failed logs…"
  gh run view "$RUN_ID" --log-failed 2>&1 | tail -n 120 || gh run view "$RUN_ID" 2>&1 | tail -n 80 || true
  dim "view: gh run view ${RUN_ID} --log-failed"
  dim "web:  https://github.com/${OWNER_REPO}/actions/runs/${RUN_ID}"
  exit $RC
fi
