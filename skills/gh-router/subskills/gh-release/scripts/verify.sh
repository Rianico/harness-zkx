#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"

phase 2 3 "Verify — lint / typecheck / test"

# detect repo type (silent — verbose only with GH_RELEASE_VERBOSE=1)
if [[ -f package.json ]]; then
  repo="node"
elif [[ -f Cargo.toml ]]; then
  repo="rust"
else
  repo="python"
fi
[[ "${GH_RELEASE_VERBOSE:-0}" == "1" ]] && dim "repo: $repo"

# Collect passed steps; print a single aggregated line on success.
# This keeps the happy path to 2 lines (phase header + aggregated result)
# instead of N per-step banners, while still showing full tail on failure.
PASSED=()

run_step() {
  local name="$1" tolerant="${2:-false}" out rc
  shift 2
  out=$(mktemp)
  set +e
  "$@" >"$out" 2>&1
  rc=$?
  set -e
  if [[ $rc -eq 0 ]]; then
    PASSED+=("$name")
    rm -f "$out"
    return 0
  fi
  if [[ "$tolerant" == "true" ]]; then
    warn "$name failed or not configured (rc=$rc)"
    tail -n 40 "$out"
    rm -f "$out"
    return 0
  fi
  tail -n 80 "$out"
  rm -f "$out"
  phase_fail 2 "$name failed"
  exit 1
}

if [[ "$repo" == "node" ]]; then
  pm="npm"
  if [[ -f pnpm-lock.yaml ]]; then
    pm="pnpm"
  elif grep -q '"packageManager"[[:space:]]*:[[:space:]]*"pnpm' package.json 2>/dev/null; then
    pm="pnpm"
  elif [[ -f pnpm-workspace.yaml ]]; then
    pm="pnpm"
  fi
  [[ "${GH_RELEASE_VERBOSE:-0}" == "1" ]] && dim "pm: $pm"
  if [[ "$pm" == "pnpm" ]]; then
    run_step "lint"      false pnpm run --silent lint
    if grep -q '"format"[[:space:]]*:' package.json 2>/dev/null; then
      run_step "format"    false pnpm run --silent format
    fi
    run_step "typecheck" false pnpm run --silent typecheck
    if grep -q '"test:coverage"[[:space:]]*:' package.json 2>/dev/null; then
      run_step "test"      false pnpm run --silent test:coverage
    else
      run_step "test"      false pnpm test
    fi
  else
    run_step "lint"      false npm run --silent lint
    run_step "typecheck" false npm run --silent typecheck
    run_step "test"      false npm test
  fi
elif [[ "$repo" == "rust" ]]; then
  run_step "clippy" false cargo clippy
  run_step "test"   false cargo test
else
  run_step "ruff check" false ruff check .
  run_step "pytest"     true uv run pytest -q
fi

if [[ ${#PASSED[@]} -gt 0 ]]; then
  # Join with " · " — single line instead of N per-step lines
  joined=""
  for n in "${PASSED[@]}"; do
    [[ -z "$joined" ]] && joined="$n" || joined="$joined · $n"
  done
  ok "$joined passed"
fi

phase_ok 2 "verification passed"
