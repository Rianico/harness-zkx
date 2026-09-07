---
name: harness-audit
description: >-
  Audits pi session JSONL for oversized bash outputs, analyses cause and triages refinable vs replaceable-by-tool vs filter vs keep for fix-or-gotcha decision. Use when trimming verbose results or hardening context-window bloat. TRIGGER: harness audit, session jsonl, bash triage, gotcha rule
arguments: target
argument-hint: |-
  <session-id-or-path> -- session id (uuid) or absolute/relative path to a pi session jsonl file
  [--threshold N] -- line threshold that marks a bash output as oversized (default: 20)
  [--json] -- emit machine-readable JSON instead of text report
  [--emit-filtered] -- write a filtered session copy alongside the report
  [--keep-head-tail N] -- when truncating, keep first/last N lines (default: 10)
---

# harness-audit

Deterministic scan for oversized `bash` tool results **plus** constructive triage. Scan identifies candidates; the model analyses, triages, and discusses fixes with you — including whether to refine scripts or add a `rules/` guard. Read-only by default; filtered output is opt-in.

## Workflow

### 1. Resolve target

Accepts either form:

- **File path** — direct `*.jsonl` (absolute or cwd-relative).
- **Session id** — uuid `01a03e51-b378-786f-819d-f570bc26497c` or filename. Resolved via `~/.pi/agent/sessions/` and `$PI_SESSIONS_DIR`; newest match wins.

```bash
uv run $SKILL_DIR/scripts/audit.py <session-id-or-path> [--threshold 20] [--json] [--emit-filtered] [--keep-head-tail 10]
```

Exit `0` ok / `1` bad args / `2` not found.

### 2. Scan (deterministic)

`audit.py` parses JSONL line-by-line (see [session-format](references/session-format.md)), pairs `bash` `toolCall`→`toolResult`, counts `toolResult.content[].text` via `splitlines()`. Only `toolName == "bash"` is measured. With `--with-context 3` (recommended for triage) it also attaches the next 3 turns (assistant `text` + subsequent `toolCall`/`toolResult` roles) after each oversized `toolResult` so you can see how the model reacted (summarized, re-dumped, looped, or recovered) — see `audit.py --help`.

> **Tmp dump?** Not by default. `--with-context` inlines a bounded preview (first 120 chars × 3 turns, plus `role/type`) in the `--json` payload; enough for step 4 without extra I/O. Use `--dump-context <dir>` only when you need full bodies for deep dive — it writes one `oversized-<line>.json` per entry to the given tmp dir (not overwritten into the session) and prints the dir path.
### 3. Report (deterministic)

### 4. Analyse — why it overflowed (model)

For each oversized entry, state in one line:

- **Root cause:** `dump` (`cat`/`nl`/`ls -R`/`env`), `broad-search` (`rg` without scope), `loop/poll`, `verbose-log` (test/build), or `legitimate-large` (known artifact).
- **Manageable?** Yes if you can intervene the producing call/site and keep intent `< threshold` — tighten flags (`pytest -q`, `rg --max-count` / `-A`, `ls | head`, `validate-deps | tail`), or edit owned `skills/*/scripts/*` to use a bounded handle. No if inherently verbose (full test/build log where bounding loses required signal) — then post-hoc truncation/filtering (`--emit-filtered` / `keep_head_tail`) is the fix.
- **Replaceable?** Orthogonal: which advanced handle replaces the bash with same intent at lower cost — `rg`→`ast_grep_search`/`symbol_search`, `cat|grep`→`read_symbol`/`module_report`/`read --offset/limit`, repeated `bash` polling→`tool feedback`/`lsp`.

Keep prose tight: `why / manageable / replaceable + tool` — no re-diagnosing scan.

### 5. Triage (model proposes, you decide)

| Bucket | Signal | Default action |
|---|---|---|
| **A — Refine script** | Dump/search/poll in owned `skills/*/scripts/*` (or tight flag in managed invocation); repeat offender; manageable=Yes & owned | Edit the owning script: add bound flag (`-q`/`--max-count`/`| head`) or replace with scoped tool; add test in `tests/harness-audit/` if reusable; re-run `uv run ruff check` + `audit.py --with-context 3` to confirm `< threshold` |
| **B — Replace bash with advanced command** | One-off exploratory bash that wasted context; manageable=Yes but unowned | Document mapping and switch next time: `ast_grep`/`lsp`/`read` handle; no script edit; optional one-line note in skill or `gotcha` if recurrent |
| **C — Filter output** | Legitimately large but context-costly log | Keep bash, use `--emit-filtered` (or lower `keep_head_tail`) |
| **D — Keep** | Rare/expected large, cost acceptable | No action |

Per entry: `bucket / confidence / cheapest fix / context saved`. Include simpler/no-change when credible; do not invent fixes when one path suffices (keel: bounded options).

### 6. Discuss & harden — user decision

Present triaged list as dialog (not auto-fix):

```
1. line 16 — `nl -ba _lib.py` (101 lines) → A — refine to `read --offset 120 --limit 20`  [saves ~80 lines]
2. line 39 — `rg except` (51 lines) → B — replace with `ast_grep_search`                     [saves ~30 lines]
```

Ask: *Which entries to (a) refine script, (b) replace bash in future, (c) keep with filtered output, or (d) keep as-is?* Default `C` for `verbose-log`; require explicit approval for `A/B` touching `skills/*/scripts/` or `rules/`.

On approval:

- **Refine script:** edit producing script (not session), replace `bash cat|rg` with scoped tool, add test in `tests/harness-audit/` when reusable, re-run `uv run ruff check` + `audit.py`.
- **Replace bash:** note advanced-tool mapping for next turn; no code change.
- **Add to `rules/common/gotcha.md`:** only when violation creates meaningful context-window risk and check can change action (keel §6). New gotcha needs evidence rule detects planted violation, narrow scope, owner, removal condition. Otherwise prefer one-off fix. Default gotchas remain shrink-only; growth is boundary decision.
## Examples

```bash
# By path
uv run $SKILL_DIR/scripts/audit.py ~/.pi/agent/sessions/.../2026-09-06T14-48-05_xxx.jsonl

# By session id
uv run $SKILL_DIR/scripts/audit.py 01a07730-d9be-73cc-b7b1-a8caa2187f49 --threshold 50

# Machine-readable + produce filtered copy
uv run $SKILL_DIR/scripts/audit.py 01a07730-d9be-73cc-b7b1-a8caa2187f49 --json --emit-filtered --keep-head-tail 8
```

## Completion

Done when every `bash` result classified, every oversized entry has `why/manageable/replaceable + bucket`, savings estimate printed, **and** user has chosen `A/B/C/D` per entry. With `--emit-filtered`, also when sibling file round-trips with same record count.
