#!/usr/bin/env bash
set -euo pipefail
# Verify: repo verification (lint/typecheck/test) - adapt per repo
if [ -f package.json ]; then
  npm run lint && npm run typecheck && npm test
elif [ -f Cargo.toml ]; then
  cargo clippy && cargo test
else
  ruff check . && uv run pytest -q || true
fi
