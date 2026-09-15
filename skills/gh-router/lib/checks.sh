#!/usr/bin/env bash
# checks.sh — verdict over a pull request's checks.
#
# Sourced, never executed. Contract (pure — no gh, no network, no logging):
#   checks_verdict reads `name<TAB>bucket` lines on stdin and prints exactly one of
#   `success` | `failure` | `pending` on stdout.
#
# Two rules the verdict must keep, both learned from a real merge that nearly landed red:
#   * EVERY check counts. The previous implementation was an inline jq allowlist naming three
#     check names (`verify`, `check`, `changelog-check`), so this repo's `tests` check was
#     invisible and `--watch --merge` reported success off the changelog check alone.
#   * Empty means pending, never success. Checks register asynchronously after a push; a PR
#     whose checks have not appeared yet is not green.
#
# `bucket` is gh's categorisation of a check run or commit status:
# pass | fail | pending | skipping | cancel. Anything unrecognised is treated as pending, so
# a new bucket upstream degrades to "keep waiting" rather than "merge".

checks_verdict() {
  local bucket total=0 failed=0 pending=0
  # The check name is consumed only to reach its bucket — the verdict never keys on a name.
  while IFS=$'\t' read -r _ bucket || [[ -n "${bucket:-}" ]]; do
    [[ -n "${bucket:-}" ]] || continue
    total=$((total + 1))
    case "$bucket" in
    fail | cancel) failed=$((failed + 1)) ;;
    pass | skipping) ;;
    *) pending=$((pending + 1)) ;;
    esac
  done
  # A single failure is reported immediately: it is the most actionable verdict and it must
  # not be masked by other checks that are still running.
  if ((failed > 0)); then
    printf 'failure'
  elif ((total == 0)) || ((pending > 0)); then
    printf 'pending'
  else
    printf 'success'
  fi
}
