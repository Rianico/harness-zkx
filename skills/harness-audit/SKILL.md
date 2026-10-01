---
name: harness-audit
description: >-
  Audits pi session JSONL for oversized bash outputs, edit failures, and dead skills; captures trigger evals and triages fixes. Use when trimming verbose results, hardening context bloat, diagnosing edit rejections, or evaluating skill discovery.
arguments: target
argument-hint: |-
  <session-id-or-path> -- session id (uuid) or absolute/relative path to a pi session jsonl file
  audit.py: [--threshold N] [--json] [--emit-filtered] [--keep-head-tail N] [--census]
  audit_edits.py: [--json] [--with-context N] [--dump-context <dir>]
  audit_skills.py: [--days N] [--json] | capture <session-id> --skill <name> --expect [trigger|no-trigger]
disable-model-invocation: true
---

# harness-audit

Deterministic scan for oversized `bash` tool results **plus** constructive triage, **and** a second workload for `edit` tool failures (hash-anchor rejections). Scan identifies candidates; the model analyses, triages, and discusses fixes with you — including whether to refine scripts or add a `rules/` guard. Read-only by default; filtered output is opt-in.

Three workloads: `audit.py` (bash oversized output), `audit_edits.py` (edit failures), and `audit_skills.py` (skill discovery & trigger capture). All resolve targets via §1 and support `--json`.
## Workflow

### 1. Resolve target

Accepts either form:

- **File path** — direct `*.jsonl` (absolute or cwd-relative).
- **Session id** — uuid `01a03e51-b378-786f-819d-f570bc26497c` or filename. Resolved via `~/.pi/agent/sessions/` and `$PI_SESSIONS_DIR`; newest match wins.

```bash
uv run $SKILL_DIR/scripts/audit.py <session-id-or-path> [--threshold 20] [--json] [--emit-filtered] [--keep-head-tail 10]
```

Exit `0` ok / `1` bad args / `2` not found / `3` scanned records but paired no bash (schema warning — *not* a clean result).

### 2. Scan (deterministic)

`audit.py` parses JSONL line-by-line (see [session-format](references/session-format.md)), pairs `bash` `toolCall`→`toolResult`, counts `toolResult.content[].text` via `splitlines()`. It accepts both record shapes — native `type == "message"` and the pi event-stream `message_end` (benchmark harness `stdout.jsonl`) — so a stream log is never read as empty. Only `toolName == "bash"` feeds the oversized table; `--census` adds a delivered-line census for every tool. A delivery-cap footer (`[Showing lines A-B of Z (50.0KB limit)…]`) yields `produced_lines` / `omitted_lines` per entry plus a session total, so produced-but-never-delivered lines are not invisible. The default text report therefore gains exactly one line — `Produced but not delivered (delivery cap): N lines omitted across M tool results, all tools` — **only when at least one result was capped**; on a truncation-free session the text report is byte-identical to the pre-census version. With `--with-context 3` (recommended for triage) it also attaches the next 3 turns (assistant `text` + subsequent `toolCall`/`toolResult` roles) after each oversized `toolResult` so you can see how the model reacted (summarized, re-dumped, looped, or recovered) — see `audit.py --help`.

> **Bash-only is not the whole budget.** In benchmark corpora `read` was 67 % of delivered tool lines vs `bash` 28 %; bash share ranged 30–67 % across observations of the same arm and tasks, and the arm's *worst* performer used the *least* bash (it leaned on `read`/`edit`). A bash-only metric ranks bash appetite, not context discipline — take `--census` before drawing cross-session conclusions.

> **Tmp dump?** Not by default. `--with-context` inlines a bounded preview (first 120 chars × 3 turns, plus `role/type`) in the `--json` payload; enough for step 4 without extra I/O. Use `--dump-context <dir>` only when you need full bodies for deep dive — it writes one `oversized-<line>.json` per entry to the given tmp dir (not overwritten into the session) and prints the dir path.

### 3. Report (deterministic)

### 4. Analyse — why it overflowed (model)

For each oversized entry, state in one line:

- **Root cause:**
  - `dump` (`cat`/`nl`/`ls -R`/`env`)
  - `broad-search` (`rg` without scope) — audit if caused by missing navigation pointer in `AGENTS.md`/`CLAUDE.md`.
  - `loop/poll` — audit if caused by missing environmental plumbing (e.g. untracked dev-server logs, missing status tool).
  - `verbose-log` (test/build runners)
  - `tool-payload` (oversized return from non-bash tool, MCP, or whole-file read).
  - `legitimate-large` (known artifact).
- **Manageable?** Yes if you can intervene the producing call/site and keep intent `< threshold` — tighten flags (`pytest -q`, `rg --max-count` / `-A`), add navigation pointer, improve environment plumbing (tee server logs to file), or edit owned `skills/*/scripts/*` to use a bounded handle. No if inherently verbose — then post-hoc truncation/filtering (`--emit-filtered` / `keep_head_tail`) is the fix.
- **Replaceable?** Orthogonal: which advanced handle replaces the bash with same intent at lower cost — `rg`→`ast_grep_search`/`symbol_search`, `cat|grep`→`read_symbol`/`module_report`/`read --offset/limit`, repeated `bash` polling→`tool feedback`/`lsp`/`tee`.
- **Existing Rule Check (No-Op Detection):** Did this violate an already-declared rule in `rules/` or `gotcha.md`? If rule was present but ignored by the model, flag it as a **No-Op**.

Keep prose tight: `why / manageable / replaceable + tool` — no re-diagnosing scan.

### 5. Triage (model proposes, you decide)

| Bucket                                     | Signal                                                                                                                        | Default action                                                                                                                                                                                                                       |
| ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **A — Refine script**                      | Dump/search/poll in owned `skills/*/scripts/*` (or tight flag in managed invocation); repeat offender; manageable=Yes & owned | Edit the owning script: add bound flag (`-q`/`--max-count`/`\| head`) or replace with scoped tool; add test in `tests/harness-audit/` if reusable; re-run `uv run ruff check` + `audit.py --with-context 3` to confirm `< threshold` |
| **B — Replace bash with advanced command** | One-off exploratory bash that wasted context; manageable=Yes but unowned                                                      | Document mapping and switch next time: `ast_grep`/`lsp`/`read` handle; no script edit; optional one-line note in skill if recurrent                                                                                                  |
| **C — Filter output**                      | Legitimately large but context-costly log                                                                                     | Keep bash, use `--emit-filtered` (or lower `keep_head_tail`)                                                                                                                                                                         |
| **D — Keep**                               | Rare/expected large, cost acceptable                                                                                          | No action                                                                                                                                                                                                                            |
| **E — Environment / Pointer fix**          | Broad search due to navigation blindness, or blind polling due to untracked daemon                                           | Add navigation pointer to root `AGENTS.md`/`CLAUDE.md`, or tee runtime daemon logs to disk                                                                                                                                           |

Per entry: `bucket / confidence / cheapest fix / context saved`. Include simpler/no-change when credible; do not invent fixes when one path suffices (keel: bounded options).

### 6. Discuss & harden — user decision

Present triaged list as dialog (not auto-fix):

```
1. line 16 — `nl -ba _lib.py` (101 lines) → A — refine to `read --offset 120 --limit 20`  [saves ~80 lines]
2. line 39 — `rg except` (51 lines) → E — add navigation pointer to AGENTS.md             [eliminates scan]
```

Ask: *Which entries to (a) refine script, (b) replace bash in future, (c) keep with filtered output, (d) keep as-is, or (e) fix environment/navigation?* Default `C` for `verbose-log`; require explicit approval for `A/B/E` touching `skills/*/scripts/` or `rules/`.

On approval:

- **Refine script:** edit producing script (not session), replace `bash cat|rg` with scoped tool, add test in `tests/harness-audit/` when reusable, re-run `uv run ruff check` + `audit.py`.
- **Replace bash:** note advanced-tool mapping for next turn; no code change.
- **Environment & Navigation:** add concise navigation pointer to root `AGENTS.md`/`CLAUDE.md`, or pipe daemon logs to file.
- **Harden vs Gotchas (Deterministic Check > Steering Rule):**
  - **Mechanical violations** (syntax, flags, unbounded dumps, missing leases, numeric anchors) → **build a deterministic check** (pre-commit hook, CI step, tool wrapper script). Never write a prose gotcha for mechanical failures.
  - **Add to `rules/common/gotcha.md`:** reserve strictly for qualitative **judgment calls** uncatchable by tools (keel §6). Requires evidence rule detects planted violation, narrow scope, owner, removal condition. Default gotchas remain shrink-only.
  - **Prune No-Ops:** If an existing rule failed to alter agent behavior during the session, prune the dead prose or convert to a hard tool blocker.

## Edit audit workload

`audit_edits.py` parses JSONL line-by-line (see [session-format](references/session-format.md)), pairs `edit` `toolCall`→`toolResult` (exact id, then `|` prefix/suffix fallback), and classifies rejections by domain error code. Read-only; exit `0` ok / `1` bad args / `2` not found.

```bash
uv run $SKILL_DIR/scripts/audit_edits.py <session-id-or-path> [--json] [--with-context 3] [--dump-context <dir>]
```

Report: total `edit` calls, successes, failures, failure rate, breakdown by code against the full registry in pi-better-edit `src/domain-errors.ts` (19 `E_*` codes; the JSON key stays `by_code`), per-file counts, plus two pattern flags — `numeric_anchor_failures` (anchors matching `/^\d+$/`, i.e. line numbers passed as hashes) and `foreign_leak_failures` (anchor served for a different file than the target). Applied-tier `W_*` notes are reported separately under `warnings` / `by_warning_code` and are never counted as failures (`W_*` means the mutation was written; `E_*` means it was rejected). With `--with-context 3` (recommended for triage) each failure carries the next 3 turns so you can see how the model reacted (re-read and retried, looped, or abandoned).

> **Marker greps overcount.** A raw `grep -o '\[E_[A-Z_]*\]'` over a session also matches codes embedded in `bash`/`read` output (e.g. bundled extension JS), so scope any marker metric to `toolName in (edit, write, undo_last_edit)`. `audit_edits.py` counts markers only inside `edit` results — the narrowest safe scope (it does not read `write`/`undo_last_edit` results).

### Triage categories for edit failures

| # | Signal | Fix |
| - | ------ | --- |
| **N — numeric line number** | `numeric_anchors` non-empty (`"833"`, `"125"`) | Never pass line numbers; `read` the file to obtain a lease, then use the served hash |
| **H — hallucinated anchor** | `E_UNKNOWN_ANCHOR` / `E_STALE_ANCHOR` / `E_UNSERVED_RANGE` without numeric signal; model inspected via `sed -n`/`grep -n` but never called `read` | `read` before `edit` — anchors require a lease |
| **F — foreign / leaked anchor** | `E_FOREIGN_ANCHOR`; `served for` path differs from target | Re-check file identity per edit in multi-file turns; re-`read` the target file |
| **B — batch abort** | `E_BATCH_ABORT` (overlapping spans in one `edits[]`) | Split into disjoint spans or sequential calls |
| **M — malformed anchor** | `E_MALFORMED_ANCHOR` (empty / wrong-shape anchor value) | Fix the anchor value at the call site; never synthesize hash strings |
| **T — target lost** | `E_TARGET_LOST` (anchor deleted in an earlier turn) | Re-`read` and re-target; don't reuse anchors across mutations |
| **P — payload / contract** | `E_BAD_PAYLOAD` (the call's `edits[]` failed the tool's shape contract) | Fix the payload shape at the call site; do not retry the same body |
| **R — path / limits** | `E_NOT_FOUND`, `E_ACCESS`, `E_UNSUPPORTED_FILE`, `E_LARGE_FILE` | Resolve the path or drop the unsupported file — not an anchor-lease problem |
| **G — guard / policy** | `E_SUSPICIOUS_TEXT`, `E_EMPTY_RANGE`, `E_NOOP_LOOP` | A guard refused the edit; inspect intent before retrying |
| **U — undo lifecycle** | `E_UNDO_STALE`, `E_UNDO_UNAVAILABLE` | The undo target expired or none is available; re-`read` and re-target |
| **W — applied-tier warning** | `W_*` under `warnings[]` — mutation was applied | Not a failure; verify the byte-exact result before trusting the edit |

Per failure: `category / confidence / cheapest fix`. Done when every failure has a category and the model shows a corrected retry (fresh `read` → valid anchors) or an explicit keep.

## Skill audit & trigger capture workload

`audit_skills.py` parses session JSONL to measure skill discovery, identify dead skills, and harvest real session friction into the trigger ledger (`~/.pi/agent/evals/<skill_name>.yaml`).

```bash
# Scan sessions for invocation counts, dead skills, and zero-skill friction sessions
uv run $SKILL_DIR/scripts/audit_skills.py [--days 30] [--json]

# Capture an agent_run step from a session into a skill's trigger eval ledger
uv run $SKILL_DIR/scripts/audit_skills.py capture <session-id-or-path> --skill <name> --expect [trigger|no-trigger] [--intent in_domain|hard_negative]
```

`audit_skills.py capture` automatically queries `git log -1` and `git status` on the skill directory to populate `snapshot.git_commit` and `snapshot.dirty`, alongside `snapshot.captured_description`.

### Triage & Discovery Categories

| Finding | Signal | Default action |
| ------- | ------ | -------------- |
| **Dead Skill** | Installed in `.agents/skills/` or `~/.pi/agent/skills/` with 0 invocations in lookback | Triage to `skill-authoring`: audit description triggers, check for missing symptom keywords, or prune |
| **Zero-Skill Friction** | High bash retries / edit loops with 0 skills loaded | Model inspects User Prompt + Error Turn to triage whether an installed skill should have triggered |
| **Eval Harvest** | Daily session encountered target task or near-miss | Capture `agent_run` observation (`user_prompt` or `tool_result`) into `~/.pi/agent/evals/<skill_name>.yaml` |

## Examples

```bash
# By path
uv run $SKILL_DIR/scripts/audit.py ~/.pi/agent/sessions/.../2026-09-06T14-48-05_xxx.jsonl

# By session id
uv run $SKILL_DIR/scripts/audit.py 01a07730-d9be-73cc-b7b1-a8caa2187f49 --threshold 50

# Machine-readable + produce filtered copy
uv run $SKILL_DIR/scripts/audit.py 01a07730-d9be-73cc-b7b1-a8caa2187f49 --json --emit-filtered --keep-head-tail 8
```

```bash
# Edit failures for the same session
uv run $SKILL_DIR/scripts/audit_edits.py 01a07730-d9be-73cc-b7b1-a8caa2187f49 --with-context 3

# Machine-readable
uv run $SKILL_DIR/scripts/audit_edits.py <session-id-or-path> --json
```

```bash
# Skill discovery audit
uv run $SKILL_DIR/scripts/audit_skills.py --days 14

# Capture rebase conflict session as positive eval case
uv run $SKILL_DIR/scripts/audit_skills.py capture 01a07730-d9be-73cc-b7b1-a8caa2187f49 --skill resolve-merge-conflicts --expect trigger --intent in_domain
```

## Completion

Done when every `bash` result classified, every oversized entry has `why/manageable/replaceable + bucket`, savings estimate printed (the `keep_head_tail`-window model — the stricter `Σ(n − threshold)` headline differs by one line per entry by definition, not a bug), truncation totals reviewed, **and** user has chosen `A/B/C/D/E` per entry. With `--emit-filtered`, also when sibling file round-trips with same record count. For edit audit: done when every edit failure has deterministic `category` N/H/F/B/T/M/P/R/G/U (or `?` for `E_UNKNOWN` / unrecognized codes with a stated reason), `W_*` rows are reported separately as applied-tier (never as failures), and the model proposes a corrected retry (read before edit, separate spans, re-read after mutation) or an explicit keep.
