#!/usr/bin/env bash
# log.sh — output and failure policy for gh-router scripts.
#
# Sourced, never executed. Owns colour, quiet mode, the phase/ok/warn/fail vocabulary, and
# the policy that an unhandled command failure aborts the script with a visible marker.
#
# Deliberately separate from repo.sh: repo.sh is a pure fact module whose stdout is consumed
# by command substitution, while this module writes to stdout for humans and installs an ERR
# trap. A script that only needs a repo slug must be able to source repo.sh alone.
#
# Respects NO_COLOR; falls back to plain when not a TTY.

set -uo pipefail

# Quiet mode: GH_RELEASE_QUIET=1 suppresses informational lines (info/dim/step and the phase
# banner bar) so harness/context-limited runs stay lean. Meaningful outcomes (ok/warn/fail/
# phase markers) always print.
_QUIET=false
[[ "${GH_RELEASE_QUIET:-0}" == "1" ]] && _QUIET=true

# --- color setup ---
if [[ -n "${NO_COLOR:-}" ]] || [[ "${TERM:-}" == "dumb" ]] || ! [[ -t 1 ]] 2>/dev/null; then
  _C_RESET=""
  _C_BOLD=""
  _C_DIM=""
  _C_RED=""
  _C_GREEN=""
  _C_YELLOW=""
  _C_BLUE=""
  _C_CYAN=""
  _C_MAGENTA=""
else
  _C_RESET=$'\033[0m'
  _C_BOLD=$'\033[1m'
  _C_DIM=$'\033[2m'
  _C_RED=$'\033[31m'
  _C_GREEN=$'\033[32m'
  _C_YELLOW=$'\033[33m'
  _C_BLUE=$'\033[34m'
  _C_CYAN=$'\033[36m'
  _C_MAGENTA=$'\033[35m'
fi

# _log <color> <prefix> <msg>
_log() {
  local color="$1" prefix="$2"
  shift 2
  printf "%s%s%s %s%s\n" "$color" "$prefix" "$_C_RESET" "$*" "$_C_RESET"
}

# Public helpers
phase() {
  # phase N M Name — e.g. phase 1 3 "Check"
  local n="$1" m="$2"
  shift 2
  printf "\n%s%s━━━ Phase %s/%s: %s ━━━%s\n" "$_C_BOLD" "$_C_CYAN" "$n" "$m" "$*" "$_C_RESET"
  if [[ "$_QUIET" != "true" ]]; then
    local bar="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    printf "%s%s%s%s\n" "$_C_DIM" "$bar" "$_C_RESET" ""
  fi
}

phase_ok() {
  # phase_ok N "detail"
  local n="$1"
  shift
  _log "$_C_GREEN" "✔" "Phase $n ok${*:+ — $*}"
}

phase_fail() {
  local n="$1"
  shift
  _log "$_C_RED" "✘" "Phase $n failed${*:+ — $*}"
}

info() {
  [[ "$_QUIET" == "true" ]] && return 0
  _log "$_C_BLUE" "→" "$*"
}
ok() { _log "$_C_GREEN" "✔" "$*"; }
warn() { _log "$_C_YELLOW" "⚠" "$*"; }
# fail — log and exit with the caller's code (default 1).
# Without the exit, `cmd || fail … 3` kept running and reported success, so documented exit
# codes never happened — a failed workflow watch returned 0.
fail() {
  local _code="${2:-1}"
  _log "$_C_RED" "✘" "$1"
  exit "$_code"
}
dim() {
  [[ "$_QUIET" == "true" ]] && return 0
  _log "$_C_DIM" "·" "$*"
}
step() {
  [[ "$_QUIET" == "true" ]] && return 0
  _log "$_C_CYAN" "▸" "$*"
}

# Ensure errors show a clear marker before set -e exits
trap 'fail "command failed: $BASH_COMMAND (line $LINENO)"' ERR
