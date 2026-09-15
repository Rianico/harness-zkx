#!/usr/bin/env bash
# repo.sh — which repository this checkout actually talks to.
#
# Sourced, never executed. Contract (kept deliberately narrow so it composes):
#   * prints ONLY the value on stdout — no logging, no colour, no banners;
#   * returns non-zero instead of printing a diagnostic, so no call can pollute stdout;
#   * installs no ERR trap and changes no shell option — a pure fact module.
#
# Why this is its own module: "which repo" is one fact, and it had three derivations in this
# skill (a helper, an inline copy in pr.sh, and bare `gh repo view`). In a multi-remote
# checkout `gh repo view` resolves to the *upstream* project, so a run lookup 404s or a
# `repository_dispatch` fires a release workflow at the wrong repo (#33).

# repo_remote_for_ref [ref] — remote that <ref> is pushed to (default: current branch).
# branch.<ref>.pushRemote -> branch.<ref>.remote -> origin.
repo_remote_for_ref() {
  local ref="${1:-}" remote=""
  [[ -n "$ref" ]] || ref=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
  if [[ -n "$ref" ]]; then
    remote=$(git config --get "branch.$ref.pushRemote" 2>/dev/null ||
      git config --get "branch.$ref.remote" 2>/dev/null || echo "")
  fi
  printf '%s' "${remote:-origin}"
}

# repo_slug_from_url <remote-url> — owner/name of an scp-style or URL-style git remote.
# Returns non-zero when the URL carries no usable owner/name, so a half-parsed URL can never
# leak through as a "slug" and be pasted into a repos/<slug>/... path.
repo_slug_from_url() {
  local slug
  slug=$(printf '%s' "${1:-}" |
    sed -E 's#^[A-Za-z][A-Za-z0-9+.-]*://##; s#^[^/@]*@##; s#^[^/:]+[:/]##; s#\.git$##; s#/+$##')
  [[ "$slug" =~ ^[^/:[:space:]]+/[^/:[:space:]]+$ ]] || return 1
  printf '%s' "$slug"
}

# repo_slug [ref] — owner/name of the repo this checkout pushes to.
#
# Derived from the push remote, NOT from `gh repo view`, which answers for the upstream/fork
# in a multi-remote checkout. `gh repo view` survives only as the last resort, when no
# configured remote parses to a slug.
#
# Usage: REPO=$(repo_slug) || fail "…" 2   # assignment inside a condition context
repo_slug() {
  local remote url slug=""
  remote=$(repo_remote_for_ref "${1:-}") || return 1
  url=$(git remote get-url --push "$remote" 2>/dev/null ||
    git remote get-url origin 2>/dev/null || echo "")
  slug=$(repo_slug_from_url "$url" 2>/dev/null || true)
  if [[ -z "$slug" ]]; then
    slug=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")
    [[ "$slug" =~ ^[^/:[:space:]]+/[^/:[:space:]]+$ ]] || return 1
  fi
  printf '%s' "$slug"
}

# default_branch [ref] — default branch of the repo this checkout pushes to.
#
# Same trap as repo_slug(): `gh repo view --json defaultBranchRef` answers for the upstream
# project, so the branch name can come from the wrong repo (upstream `master` vs fork `main`).
# Resolve the slug from the push remote first, then ask that repo.
#
# Usage: BASE=$(default_branch) || BASE=main
default_branch() {
  local repo
  repo=$(repo_slug "${1:-}") || return 1
  gh api "repos/$repo" --jq '.default_branch' 2>/dev/null || return 1
}
