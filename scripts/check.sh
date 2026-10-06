#!/usr/bin/env bash
# scripts/check.sh — the four authoritative quality gates, in CI order.
# Stops at the first failure and names the failed gate.
set -euo pipefail

# Grade this script's own repo, never the caller's git root: `git rev-parse`
# followed the caller's cwd/GIT_DIR, so check.sh linted the wrong tree.
# `set -e` makes a failed resolution abort loudly instead of grading a wrong tree.
# `unset CDPATH` stops a shadowing CDPATH from diverting the relative `cd` below.
# `cd -P`/`pwd -P` resolve the root physically, so the printed root is the true
# directory (a symlinked entry point cannot attest the directory it was linked into).
unset CDPATH
SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -P "$SCRIPT_DIR/.." && pwd -P)"
# Loud ownership check: a wrong tree must fail, never attest. The root's
# pyproject.toml must name this project.
HARNESS_NAME="claude-skills-harness"
ROOT_PYPROJECT="$REPO_ROOT/pyproject.toml"
if [ ! -f "$ROOT_PYPROJECT" ] ||
  ! grep -Eq "^name = \"${HARNESS_NAME}\"" "$ROOT_PYPROJECT"; then
  echo "refusing: $REPO_ROOT is not the ${HARNESS_NAME} repo" >&2
  exit 3
fi
cd "$REPO_ROOT"
echo "==> checking $REPO_ROOT"

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
  run_gate 4 uv run pytest
fi

if [ "$SKIP_TESTS" -eq 1 ]; then
  echo "3/4 gates passed (pytest skipped: --skip-tests)"
else
  echo "All gates passed."
fi
