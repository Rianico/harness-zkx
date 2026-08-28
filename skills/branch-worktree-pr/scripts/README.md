# branch-worktree-pr scripts

Deterministic Python shims so the model calls `uv run scripts/<name>.py` with args instead of building shell commands. Use plain words: branch, copy, merge, conflict, fix, test, check, file, folder.

All shims are `#!/usr/bin/env python3` with inline `# /// script` (`requires-python = ">=3.12"`, stdlib only, `uv run` auto-installs), typed, testable, and delegate to `wt`/`gh`/`git` via `subprocess.run(list, ...)` (no `shell=True` for user inputs). Gate is trusted single writer `.config/wt.toml [pre-merge].gate` — executed only via `wt merge` or `run_gate()`.

Shared helpers live in `_lib.py` (`detect_stack_gate()`, `scaffold_wt_config()`, `read_gate()`, `wt_list()`, `git_status_clean()`, `current_branch()`, `run()`, `run_gate()`). Phases keep 1:1 script mapping but share this typed boundary.

> [!tip] Worktree vs raw
> `wt` stays final gate. Shims never re-implement `wt switch`/`wt merge`/`copy-ignored`/`hash_port` — they delegate.

## When to call (maps to workflow phases)

| Phase | Script (uv run)                                            | What it does                                                                                                                                                                                                                                                                                                                                                                       |
| ----- | ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0     | `uv run scripts/claim_gate.py <issue-number>`              | Check ticket is unblocked and not assigned (`gh issue view --json assignees,blockedBy`), then `gh issue edit --add-assignee @me`. Warns if `.scratch` exists (pluggable tracker). Exit non-zero if blocked.                                                                                                                                                                        |
| 1     | `uv run scripts/create_target.py <branch> [base]`          | `git switch -c <branch> <base>` (default `origin/main`) and check `git branch --show-current` and `wt list` current. Stays in current folder.                                                                                                                                                                                                                                      |
| 2     | `uv run scripts/make_copy.py <child-branch> <base-branch>` | `wt switch --create <child> --base <base> --no-cd --yes`, check `wt list` exact branch match and `git -C <path> branch --show-current`, print absolute path. Stays on parent folder.                                                                                                                                                                                                                                                               |
| 2*    | `uv run scripts/self_check.py <branch> [expected-path]` | Subagent phase-0 admission gate: verify cwd is the expected worktree path on the expected branch — never the base branch dir. Exit 0 = ok; exit 1 = wrong worktree, prints hint, agent edits nothing and returns BLOCKED. Run inside the copy by each dispatched worker before touching any file.                                                          |
| 4     | `uv run scripts/verify_parent.py`                          | Read `.config/wt.toml` `[pre-merge].gate` (auto-scaffold from `references/wt-template.toml` via `detect_stack_gate()` on first run per ADR — Cargo > pyproject > package.json > deno > bun; unknown → fail loud). Execute gate, then `git diff --check` and `git status` clean (allows `.lsz/tmp`, `tmp/pi-open-tui`). Use after all copies merged.                                |
| 5     | `uv run scripts/check_history.py`                          | `git log --oneline --no-merges origin/main..HEAD` (fallback to `merge-base`/`main`/`HEAD -n 20`), and `CHANGELOG.md` has one bullet under `## [Unreleased]` with `### Added\|Changed\|Fixed\|Removed` and `(#<issue>)` or `by @`. Run before PR.                                                                                                                                   |
| 6     | `uv run scripts/open_pr.py <branch> <base> <issue-number>` | `git push -u origin <branch>`, `gh pr create --fill --base <base>` ensuring body ends `Closes #<issue>` (via `gh pr list --head`/`gh pr view` + `gh pr edit` if needed), then `gh pr view` and `git diff --check` (fixed bug: was `gh pr diff --check`). Verify `CHANGELOG.md` still has `[Unreleased]`.                                                                           |
| —     | `uv run scripts/worktree.py <subcommand>`                  | Dispatcher forwarding to same impl modules: `claim`, `create-target`, `make-copy`, `self-check`, `merge-copy`, `verify`, `check-history`, `open-pr`. Also available at `uv run scripts/worktree.py` (root).                                                                                                                                                      |
### _lib.py — typed boundary (single writer pattern)

- `detect_stack_gate(cwd?) -> str | None` — sniff `Cargo.toml` → `cargo test && cargo clippy -- -D warnings`; `pyproject.toml` → `uv run ruff check . && uv run basedpyright && uv run pytest -q`; `package.json` → `npm run typecheck && npm test`; `deno.json` → `deno task check && deno test`; `bun.lockb` → `bun run typecheck && bun test`; else `None`.
- `scaffold_wt_config(template, dest) -> str` — copy `references/wt-template.toml` → `.config/wt.toml` patched gate, ensure parent dirs, return gate; raise `FileNotFoundError` with actionable message when unknown stack.
- `read_gate() -> str` — parse `gate = "..."` via `tomllib` else regex; if absent scaffold once; if parse fails and file exists raise.
- `wt_list() -> list[Worktree]` — `wt list --format=json` (parsed, validated `Worktree(branch, path, is_current)`) fallback to `git worktree list --porcelain` (correct `worktree <path>` / `branch refs/heads/<name>` parsing).
- `git_status_clean(allow=[.lsz/tmp, tmp/pi-open-tui]) -> tuple[bool, list[str]]`, `run(cmd: list[str], cwd?)`, `ensure_clean_worktree()`, `current_branch()`, `run_gate(gate, cwd?)` (trusted `shell=True` only for `wt.toml` gate).

## Safety notes

- All paths use `Path` and list args — quoted in shell is not needed; no `shell=True` with user input.
- `wt` always called with `--yes` for non-interactive use; `wt list` validated before use.
- Fixer rebase uses `GIT_EDITOR=true GIT_SEQUENCE_EDITOR=true git -C <copy-path> rebase --continue` to avoid editor; router never rebases.
- Gate string is trusted (single writer `.config/wt.toml`); only `run_gate()` uses `shell=True`; all other subprocess calls use list args.
- Exit code 0 = ok, 2 = conflict needs fixer, 1 = gate fail — treat as blocker.
- Auto-scaffold happens once: first `read_gate()` sniffs stack and writes `.config/wt.toml`; after that `wt.toml` is only source; no runtime sniffing.

## Example run (plain words)

```bash
uv run scripts/claim_gate.py 23
uv run scripts/create_target.py map/my-work origin/main
COPY=$(uv run scripts/make_copy.py feat/my-work--part map/my-work)
# inside $COPY, before editing anything — phase-0 self-check:
uv run scripts/self_check.py feat/my-work--part "$COPY"   # must exit 0
# work happens inside $COPY via workers
uv run scripts/merge_copy.py "$COPY" map/my-work
uv run scripts/verify_parent.py
uv run scripts/check_history.py
uv run scripts/open_pr.py map/my-work main 22
# — or via dispatcher —
uv run scripts/worktree.py claim 23
uv run scripts/worktree.py create-target map/my-work origin/main
uv run scripts/worktree.py make-copy feat/my-work--part map/my-work
uv run scripts/worktree.py self-check feat/my-work--part "$COPY"  # inside copy, phase 0
uv run scripts/worktree.py merge-copy "$COPY" map/my-work
uv run scripts/worktree.py verify
uv run scripts/worktree.py check-history
uv run scripts/worktree.py open-pr map/my-work main 22
```

## Verification

```bash
uv run ruff check skills/branch-worktree-pr/scripts/
uv run basedpyright skills/branch-worktree-pr/scripts/
uv run pytest -q  # when tests exist in tests/branch-worktree-pr/
```
