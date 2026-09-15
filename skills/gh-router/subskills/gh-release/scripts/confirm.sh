#!/usr/bin/env bash
# confirm.sh — post-release verification in one call. Read-only.
#
#   release   v2.0.0 published 2026-09-12  <url>
#   tag       v2.0.0 → 5ab33ddb (annotated) · reachable from main
#   main      3175095f <subject>
#   changelog ## [Unreleased] L7 · ## [2.0.0] L17
#
# Usage: confirm.sh [--tag vX.Y.Z] [--base main]
# Exit: 0 verified | 1 tag not reachable from base | 2 usage | 3 gh unavailable
# Requires: Bash >=4.4, gh, git

set -Eeuo pipefail
shopt -s inherit_errexit 2>/dev/null || true

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LIB_DIR="$(cd "$SCRIPT_DIR/../../../lib" && pwd)"
# shellcheck source=../../../lib/log.sh
source "$LIB_DIR/log.sh"
# log.sh sets -uo pipefail; re-assert strictness after sourcing.
set -Eeuo pipefail
IFS=$'\n\t'

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  sed -n '2,11p' "$0" | sed 's/^# \?//'
  exit 0
fi

command -v gh >/dev/null 2>&1 || fail "gh CLI not found" 3

TAG=""
BASE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
  --tag)
    TAG="$2"
    shift 2
    ;;
  --base)
    BASE="$2"
    shift 2
    ;;
  -h | --help)
    sed -n '2,11p' "$0" | sed 's/^# \?//'
    exit 0
    ;;
  *) shift ;;
  esac
done

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || fail "not a git repository" 2
BASE="${BASE:-main}"
git fetch -q origin "$BASE" --tags 2>/dev/null || true
[[ -n "$TAG" ]] || TAG="$(git describe --tags --abbrev=0 "origin/$BASE" 2>/dev/null || true)"
[[ -n "$TAG" ]] || fail "no tag found — pass --tag vX.Y.Z" 2

release_json="$(gh release view "$TAG" --json tagName,isDraft,isPrerelease,publishedAt,url 2>/dev/null || true)"
if [[ -n "$release_json" ]]; then
  printf '%s' "$release_json" | python3 -c '
import json,sys
d=json.load(sys.stdin)
kind = "draft" if d["isDraft"] else ("pre" if d["isPrerelease"] else "published")
tag = d["tagName"]
when = (d.get("publishedAt") or "")[:10]
url = d.get("url") or ""
print("release   " + tag + " " + kind + " " + when + "  " + url)
'
else
  warn "no GitHub release for $TAG"
fi

tag_type="$(git cat-file -t "$TAG" 2>/dev/null || echo missing)"
tag_sha="$(git rev-parse --short "${TAG}^{commit}" 2>/dev/null || echo '?')"
if git merge-base --is-ancestor "${TAG}^{commit}" "origin/$BASE" 2>/dev/null; then
  reachable="reachable from $BASE"
else
  reachable="NOT reachable from $BASE"
fi
printf '%s\n' "tag       $TAG → $tag_sha ($tag_type) · $reachable"

printf '%s\n' "main      $(git log -1 --pretty='%h %s' "origin/$BASE")"

if [[ -f CHANGELOG.md ]]; then
  sections="$(grep -nE '^## ' CHANGELOG.md | head -2 | sed 's/\](.*//; s/^\([0-9]*\):/L\1 /' | paste -sd' · ' -)"
  printf '%s\n' "changelog $sections"
fi

git merge-base --is-ancestor "${TAG}^{commit}" "origin/$BASE" 2>/dev/null || exit 1
ok "release $TAG verified"
