#!/usr/bin/env bash
# _common.sh — shared log helpers for gh-release phases
# Usage: source "$(cd "$(dirname "$0")" && pwd)/_common.sh"
# Respects NO_COLOR; falls back to plain when not a TTY.

set -uo pipefail

# Quiet mode: GH_RELEASE_QUIET=1 suppresses informational lines (info/dim/step and
# the phase banner bar) so harness/context-limited runs stay lean. Meaningful
# outcomes (ok/warn/fail/phase markers) always print.
_QUIET=false
[[ "${GH_RELEASE_QUIET:-0}" == "1" ]] && _QUIET=true

# --- color setup ---
if [[ -n "${NO_COLOR:-}" ]] || [[ "${TERM:-}" == "dumb" ]] || ! [[ -t 1 ]] 2>/dev/null; then
  _C_RESET=""; _C_BOLD=""; _C_DIM=""; _C_RED=""; _C_GREEN=""; _C_YELLOW=""; _C_BLUE=""; _C_CYAN=""; _C_MAGENTA=""
else
  _C_RESET=$'\033[0m'; _C_BOLD=$'\033[1m'; _C_DIM=$'\033[2m'
  _C_RED=$'\033[31m'; _C_GREEN=$'\033[32m'; _C_YELLOW=$'\033[33m'
  _C_BLUE=$'\033[34m'; _C_CYAN=$'\033[36m'; _C_MAGENTA=$'\033[35m'
fi

# _log <color> <prefix> <msg>
_log() {
  local color="$1" prefix="$2"; shift 2
  printf "%s%s%s %s%s\n" "$color" "$prefix" "$_C_RESET" "$*" "$_C_RESET"
}

# Public helpers
phase() {
  # phase N M Name — e.g. phase 1 3 "Check"
  local n="$1" m="$2"; shift 2
  local name="$*"
  local bar="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  printf "\n%s%s━━━ Phase %s/%s: %s ━━━%s\n" "$_C_BOLD" "$_C_CYAN" "$n" "$m" "$name" "$_C_RESET"
  if [[ "$_QUIET" != "true" ]]; then
    local bar="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    printf "%s%s%s%s\n" "$_C_DIM" "$bar" "$_C_RESET" ""
  fi

}

phase_ok() {
  # phase_ok N "detail"
  local n="$1"; shift
  _log "$_C_GREEN" "✔" "Phase $n ok${*:+ — $*}"
}

phase_fail() {
  local n="$1"; shift
  _log "$_C_RED" "✘" "Phase $n failed${*:+ — $*}"
}

info()  { [[ "$_QUIET" == "true" ]] && return 0; _log "$_C_BLUE"   "→" "$*"; }
ok()    { _log "$_C_GREEN"  "✔" "$*"; }
warn()  { _log "$_C_YELLOW" "⚠" "$*"; }
fail()  { _log "$_C_RED"    "✘" "$*"; }
dim()   { [[ "$_QUIET" == "true" ]] && return 0; _log "$_C_DIM"    "·" "$*"; }
step()  { [[ "$_QUIET" == "true" ]] && return 0; _log "$_C_CYAN"   "▸" "$*"; }

# repo_slug — owner/name of the release repo.
#
# Derived from the remote this checkout actually pushes to (branch.<ref>.pushRemote ->
# branch.<ref>.remote -> origin), NOT from `gh repo view`: with an upstream/fork remote
# configured, `gh repo view` can resolve to the upstream repo and this script would then
# dispatch a release event at the wrong project. check.sh is origin-centric too, so the
# release target and the commit range under check agree by construction.
#
# Usage: REPO=$(repo_slug) || exit 2
repo_slug() {
  local ref remote url slug
  ref=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
  remote=""
  if [[ -n "$ref" ]]; then
    remote=$(git config --get "branch.$ref.pushRemote" || git config --get "branch.$ref.remote" || echo "")
  fi
  [[ -z "$remote" ]] && remote=origin
  url=$(git remote get-url --push "$remote" 2>/dev/null || git remote get-url origin 2>/dev/null || echo "")
  # Handle SCP-style (git@host:owner/name) AND URL-style (scheme://[user@]host/owner/name).
  slug=$(printf '%s' "$url" \
    | sed -E 's#^[A-Za-z][A-Za-z0-9+.-]*://##; s#^[^/@]*@##; s#^[^/:]+[:/]##; s#\.git$##; s#/+$##')
  # A URL that failed to parse must NOT leak through as a "slug" — validate shape.
  if [[ ! "$slug" =~ ^[^/:[:space:]]+/[^/:[:space:]]+$ ]]; then
    slug=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")
  fi
  [[ -z "$slug" ]] && return 1
  printf '%s' "$slug"
}

# Ensure errors show a clear marker before set -e exits
trap 'fail "command failed: $BASH_COMMAND (line $LINENO)"' ERR
