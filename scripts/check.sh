#!/usr/bin/env bash
# scripts/check.sh — the four authoritative quality gates, in CI order.
# Stops at the first failure and names the failed gate.
set -euo pipefail

REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

usage() {
  echo "usage: scripts/check.sh [--skip-tests]" >&2
}

SKIP_TESTS=0
case "${#}" in
  0) ;;
  1)
    if [ "${1}" = "--skip-tests" ]; then
      SKIP_TESTS=1
    else
      usage
      exit 2
    fi
    ;;
  *)
    usage
    exit 2
    ;;
esac

run_gate() {
  local number="$1"
  shift
  echo "==> [gate ${number}/4] $*"
  if ! "$@"; then
    echo "FAILED: gate ${number}/4 -> $*" >&2
    exit 1
  fi
}

run_gate 1 uv run ruff check .
run_gate 2 uv run ruff format --check .
run_gate 3 uv run basedpyright --warnings

if [ "$SKIP_TESTS" -eq 1 ]; then
  echo "==> [gate 4/4] SKIPPED: uv run pytest was skipped (--skip-tests)"
else
  run_gate 4 env HARNESS_CHECK_GATE=1 uv run pytest
fi

echo "All gates passed."
