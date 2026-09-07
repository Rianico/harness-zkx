#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"

phase 2 3 "Verify — lint / typecheck / test"

# detect repo type once
if [[ -f package.json ]]; then
  repo="node"
elif [[ -f Cargo.toml ]]; then
  repo="rust"
else
  repo="python"
fi
info "repo type: $repo"

# Run a verification step, printing ONLY a concise result on success and the
# output tail on failure — command output (lint warnings, test details) is
# unrelated noise on the happy path and would flood the context window.
run_step() {
  local name="$1" tolerant="${2:-false}" out rc
  shift 2
  step "$name"
  out=$(mktemp)
  set +e
  "$@" >"$out" 2>&1
  rc=$?
  set -e
  if [[ $rc -eq 0 ]]; then
    ok "$name passed"
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
  run_step "lint"     false npm run --silent lint
  run_step "typecheck" false npm run --silent typecheck
  run_step "test"     false npm test
elif [[ "$repo" == "rust" ]]; then
  run_step "clippy" false cargo clippy
  run_step "test"   false cargo test
else
  run_step "ruff check" false ruff check .
  run_step "pytest"     true uv run pytest -q
fi

phase_ok 2 "verification passed"