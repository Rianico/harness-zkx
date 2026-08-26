# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Entries link to related issues/PRs inline where tracked: `([#N](https://github.com/.../issues/N))` — entries with no tracked issue stay linkless.

## [Unreleased]

### Added

- Branch-worktree Python shims with `wt` gate delegation and auto-scaffold — replace bash shims with typed Python delegates (`_lib.py` typed boundary, `detect_stack_gate`, `read_gate`, `wt_list`), auto-scaffold `.config/wt.toml` once per stack (Rust/Python/TypeScript), gate single writer `wt.toml`, `wt merge` is final gate, dispatcher `worktree.py` (ADR 0013).

### Changed

- `branch-worktree-pr` SKILL.md phases updated to `uv run scripts/...py` (`claim_gate`, `create_target`, `make_copy`, `merge_copy`, `verify_parent`, `check_history`, `open_pr`), fix `gh pr diff --check` → `git diff --check`, update topology and dispatch table for module fan-out.
