---
name: rust-scaffolding
description: >-
  Rust project scaffolding with Cargo, rust-toolchain, and fmt/clippy/test wiring. Use when initializing or retrofitting a Rust repo or selecting its toolchain. TRIGGER: rust scaffold, cargo, rust-toolchain, clippy
metadata:
  managed-by: scaffold
---

# Rust Scaffold

Projection of the scaffold spine onto Rust. Declared runtime is `cargo` + `rust-toolchain.toml`; verification is `cargo fmt --check`, `cargo clippy`, `cargo test`.

## Declared Runtime

Per `development-patterns.md` §3:

- Single-runtime Rust: `cargo` + `rust-toolchain.toml`; commit both `Cargo.toml` and `rust-toolchain.toml`.
- Multi-runtime (Rust + Python/Node): `asdf` + `.tool-versions`; `asdf install` syncs all.

## Deterministic Artifacts — Tool Owns Bytes

Source of truth is `$SKILL_DIR/scripts/scaffold.py` (`RUST_TOOLCHAIN_TOML`, `CARGO_TOML_TMPL`) — run `uv run $SKILL_DIR/scripts/scaffold.py --flavor rust --dry-run` to preview.

```bash
uv run $SKILL_DIR/scripts/scaffold.py --flavor rust --project-name <name>
uv run $SKILL_DIR/scripts/scaffold.py --flavor rust --project-name <name> --dry-run
```

Pure-deterministic: `rust-toolchain.toml` (`stable` + `rustfmt`/`clippy`), `.gitignore` dedup (`GITIGNORE_GIT` + `target/`).

Mixed (script warns → proofread): `Cargo.toml` (`{{project_name}}` normalized to kebab-case, edition `2021`), `AGENTS.md` `### Runtime` pointer. Script warns if name normalized and on `AGENTS.md` 3-section preservation.

Byte view: `uv run $SKILL_DIR/scripts/scaffold.py --flavor rust --dry-run` (tool owns bytes).

## Steps — Tool Owns Determinism

1. Generate: `uv run $SKILL_DIR/scripts/scaffold.py --flavor rust --project-name <name>` (warns on kebab-case normalization).
2. Install: `cargo fetch`.
3. Proofread mixed warnings: `Cargo.toml` name/edition, `AGENTS.md` pointer.
4. Verify: `uv run $SKILL_DIR/scripts/scaffold.py --flavor rust --dry-run` + `cargo fmt --check && cargo clippy -- -D warnings && cargo test`

> [!tip] Verification — before every push/PR
>
> - `cargo fmt --check && cargo clippy -- -D warnings && cargo test` — if any fails → `BLOCKED`
> - Clean-build (`cargo clean && cargo test`) after toolchain or `Cargo.toml` change

## Grilling Selection

If Dialog 2 selected Tests and Dialog 3 selected 80%/90%/Other, add `--with-coverage --coverage-threshold <80|90|custom>`. Example: `uv run $SKILL_DIR/scripts/scaffold.py --flavor rust --with-coverage --coverage-threshold 80`. Without coverage, generator writes plain `Cargo.toml`/`cargo test` path and omits `llvm-cov` wiring. Gate is optional leaf — config stays byte-identical.

## Relation to Other Subskills

- Git contract stays canonical in `$SKILL_DIR/subskills/git-scaffolding/SKILL.md`; Rust does not redeclare it.
- CI wiring for Rust lives in `$SKILL_DIR/subskills/ci-scaffolding/SKILL.md` — Rust CI job runs `cargo test` inside the shared verify gate.
