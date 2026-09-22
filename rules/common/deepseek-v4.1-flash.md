# DeepSeek-v4.1-Flash — Tool Discipline Guardrails

Evidence: harness audit of `2026-09-21T04-33-12-559Z_01a0c23d-4d6e-7446-bb6e-906b7b4217c8.jsonl` — 232 bash calls, 105 oversized results (7,568 lines / ~56k wasted tokens), 25 edit failures (16.4%). Root cause throughout: bypassing dedicated tools (`read`) for bash substitutes, then editing without leases. Fix at source, do not route around.

---

## 1) Never inspect file contents with bash — always use `read`

**When:** inspecting files, examining code lines, or preparing an edit.

**Don't:** `sed -n '...p'`, `cat file`, `head`, `tail` via bash to read code (audit: 78 `sed -n` + 14 `cat` calls, zero leases granted).

**Do:** `read` with `{ path, offset, limit }`. `edit` requires content-addressed 3-char hashes and session leases granted strictly by `read`. Bypassing `read` causes `E_UNKNOWN_ANCHOR` / `E_MALFORMED_ANCHOR` rejections.

**Check:** transcript shows no `sed -n` / `cat` / `head` / `tail` used to inspect source files when `read` is available.

---

## 2) Scope exploratory searches — prevent unbounded `rg` / `grep` bloat

**When:** searching symbol definitions, error codes, usages, or patterns across the codebase.

**Don't:** unconstrained `rg <query>` / `grep -r <query>` dumping dozens or hundreds of lines into context (audit: 65 calls feeding the 7,568-line bloat).

**Do:** constrain every search — `-m <limit>` / `--max-count`, `-t ts` or type flags, subdirectory paths. Follow hits with `read` around the target offset to acquire valid hashes before editing.

**Check:** every `rg` / `grep` carries `-m` / `--max-count` or tight path constraints; no multi-hundred-line search outputs in transcript.

---

## 3) Keep build, lint, and test output bounded

**When:** running tests, linters, or typecheck (`pnpm test`, `vitest`, `pytest`, `tsc`).

**Don't:** broad commands dumping full passing suites or verbose traces into context.

**Do:** target specific files (`vitest run path/to/file.test.ts`), quiet/compact flags (`-q`, `--reporter=compact`), or pipe to `tail -n 30` for pass/fail status.

**Check:** test invocations target individual files or use bounded reporting; no thousand-line green runs in transcript.

---

## 4) Anchors are 3-char hashes from `read` — never line numbers or foreign anchors

**When:** building `edits: [{ anchor_from, anchor_to, replace_with }]`.

**Don't:** line numbers (`"833"`, `"125"` → `E_MALFORMED_ANCHOR`), identifiers (`"inTransaction"`), or anchors copied from another file (`E_FOREIGN_ANCHOR` — audit: 4 cross-file leaks).

**Do:** copy exclusively the 3-char alphanumeric hash before `│` from the `read` output of the exact file being edited. Re-`read` after any mutation; never reuse anchors across edits.

**Check:** every anchor is exactly 3 alphanumeric chars matching the target file's served lines; `audit_edits.py` reports zero `numeric_anchor_failures` and zero `foreign_leak_failures`.
