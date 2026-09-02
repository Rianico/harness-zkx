#!/usr/bin/env bash
set -euo pipefail
# Check: clean tree and conventional commits
if [ -n "$(git status --porcelain | grep -v -E '^\?\? \.lsz/tmp|^\?\? coverage|^\?\? node_modules')" ]; then
  echo "tree not clean" >&2
  git status --porcelain
  exit 1
fi
if [ "$(git branch --show-current)" != "main" ]; then
  echo "not on main: $(git branch --show-current)" >&2
  exit 1
fi
npx commitlint --from=origin/main --to=HEAD --verbose
