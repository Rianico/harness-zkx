#!/usr/bin/env bash
set -euo pipefail
# Deterministic gate runner for scaffold skill validation.
# Tool owns deterministic verification; model owns intent.
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VALIDATOR="$SKILL_DIR/../ai-engineering-expert/subskills/skill-authoring/scripts/validate-deps.py"
if [[ ! -f "$VALIDATOR" ]]; then
  VALIDATOR="$(cd "$SKILL_DIR/../.." && pwd)/skills/ai-engineering-expert/subskills/skill-authoring/scripts/validate-deps.py"
fi
echo "== validate-deps check =="
uv run "$VALIDATOR" check
echo "== validate-deps lint =="
uv run "$VALIDATOR" lint
echo "== validate-deps context-check =="
uv run "$VALIDATOR" context-check || true
echo "== related scaffold =="
uv run "$VALIDATOR" related scaffold || true
echo "== scaffold dry-run gates (tool owns bytes) =="
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT
uv run "$SKILL_DIR/scripts/scaffold.py" --flavor git --project-name demo --dry-run --cwd "$TMPDIR" >/tmp/scaffold-git-dryrun.log 2>&1 || true
uv run "$SKILL_DIR/scripts/scaffold.py" --flavor python --project-name demo --dry-run --cwd "$TMPDIR" >/tmp/scaffold-python-dryrun.log 2>&1 || true
uv run "$SKILL_DIR/scripts/scaffold.py" --flavor rust --project-name demo --dry-run --cwd "$TMPDIR" >/tmp/scaffold-rust-dryrun.log 2>&1 || true
uv run "$SKILL_DIR/scripts/scaffold.py" --flavor ci --ci-variant python --dry-run --cwd "$TMPDIR" >/tmp/scaffold-ci-dryrun.log 2>&1 || true
echo "dry-run logs: /tmp/scaffold-*-dryrun.log (mixed warnings on stderr are expected)"
cat /tmp/scaffold-git-dryrun.log || true
