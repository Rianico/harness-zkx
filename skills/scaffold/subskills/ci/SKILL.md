---
name: ci
description: >-
  Git CI scaffolding with pinned GitHub Actions verify+release and on-demand dispatch. Use when wiring CI gates, retrofitting workflows, or standardizing verification. TRIGGER: ci scaffold, github actions, verify gate, release workflow
metadata:
  managed-by: scaffold
---

# CI Scaffold

Owns the Git CI projection of the scaffold spine. Git owns the conventional-commit contract; CI owns the verification gate and the on-demand release dispatch.

## Deterministic Artifact — Tool Owns Bytes

Source is `$SKILL_DIR/scripts/scaffold.py` (`RELEASE_YML`, `CI_PYTHON_VERIFY_YML`, `CI_RUST_VERIFY_YML`) — run `uv run $SKILL_DIR/scripts/scaffold.py --flavor ci --ci-variant <node|python|rust> --dry-run` to preview.

```bash
uv run $SKILL_DIR/scripts/scaffold.py --flavor ci --ci-variant node     # Node verify (default, same as git)
uv run $SKILL_DIR/scripts/scaffold.py --flavor ci --ci-variant python   # Python verify (setup-uv + ruff/basedpyright/pytest)
uv run $SKILL_DIR/scripts/scaffold.py --flavor ci --ci-variant rust     # Rust verify (rust-toolchain + fmt/clippy/test)
uv run $SKILL_DIR/scripts/scaffold.py --flavor ci --ci-variant python --dry-run
```

Pure-deterministic: `.github/workflows/release.yml` per variant (pinned SHA `checkout@11d596...` + `setup-node@49933...`, `zizmor: ignore` justified, `contents: read` → `release` escalates `write/id-token`, `needs: verify`).

- On-demand dispatch is the default: `repository_dispatch` (`semantic-release`) + `workflow_dispatch` only — no `push: tags` auto-release.
- Language-specific verify steps live in the variant; multi-runtime uses matrix (`needs: [verify-node, verify-python]`). See `uv run $SKILL_DIR/scripts/scaffold.py --flavor ci --dry-run` for byte view.

### Language-Specific Verify Steps

- Python projection: replace `npm ci`/`npm test` with `uv sync` + `uv run ruff check . && uv run basedpyright && uv run pytest` inside the same `verify` job (or a matrix job when multi-runtime).
- Rust projection: `cargo fmt --check && cargo clippy -- -D warnings && cargo test` inside `verify`.
- Multi-runtime: `asdf install` + matrix, or split jobs `verify-node`/`verify-python`/`verify-rust` with `needs: [verify-node, verify-python]` on `release`.

Matrix preview: `uv run $SKILL_DIR/scripts/scaffold.py --flavor ci --dry-run` (tool owns bytes).

## Steps — Tool Owns Determinism

1. Generate: `uv run $SKILL_DIR/scripts/scaffold.py --flavor ci --ci-variant <node|python|rust>` (or `--dry-run`), optionally `--cwd`.
2. Ensure `verify` precedes `release` via `needs: verify`; `release` holds only `write`/`id-token` perms (enforced by script template).
3. Wire pre-merge gate docs: `CONTRIBUTING.md` → `npm run lint && npm run typecheck && npm test` (or `uv`/`cargo` equiv) — see `$SKILL_DIR/subskills/git/SKILL.md`.
4. Verify: `uv run $SKILL_DIR/scripts/scaffold.py --flavor ci --dry-run` + `yamllint .github/workflows/release.yml` and `zizmor .github/workflows/release.yml`

> [!tip] Verification — before merging workflow changes
>
> - `yamllint` / `zizmor` / `actionlint` if installed — if any fails → `BLOCKED`
> - Permissions are `contents: read` at workflow top; `release` job escalates minimally

## Grilling Selection

If Dialog 3 selected coverage, add `--with-coverage --coverage-threshold <n>` to the `ci` invocation. Example: `uv run $SKILL_DIR/scripts/scaffold.py --flavor ci --ci-variant python --with-coverage --coverage-threshold 80` (pytest --cov gate) or `--ci-variant rust --with-coverage` (llvm-cov). Without coverage, omit flag — verify runs without `fail_under`. Formatter/linter/type/test leaves do not change CI file bytes.

## Relation to Other Subskills

- Do not duplicate `.releaserc.json` / `CONTRIBUTING.md` / `commitlint.config.js` — canonical in `$SKILL_DIR/subskills/git/SKILL.md`.
- Runtime files (`pyproject.toml`, `rust-toolchain.toml`) stay canonical in their language subskills.

## Arguments

- `--dry-run` — print workflow diff without writing
- `--matrix` — generate multi-runtime verify matrix
