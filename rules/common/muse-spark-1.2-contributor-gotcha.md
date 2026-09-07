# Gotcha — Harness Context Bloat (muse-spark-1.2-contributor)

Model-specific hardening from harness-audit. Load unconditionally — `rules/common` is always on. Patterns observed with `PI_MODEL=muse-spark-1.2-contributor` but cost all models.

Evidence: session `01a07b5d-3e57-7852-956d-fd685d18a228` — 11/15 bash oversized (878/915 lines). Biggest win: `cat SKILL.md | head` (299 lines → 20). See `uv run $SKILL_DIR/scripts/audit.py 01a07b5d --threshold 20 --with-context 3`.

Owner: harness-audit triage. Removal: when audit shows <2 oversized/100 bash over 30 days or pattern drops from top-3.

---

## 5) Skill/doc dump — `cat … | head` bloats context

**When:** need 1–4 skills/docs to read.

**Don't:** `cat skills/*/SKILL.md | head -n 60` / `cat file | head` / `ls -R` — in session 01a07b5d line 17 dumped 299 lines (23k chars) for 4 skills; line 13 dumped `ls -R` (50 lines) for discovery.

**Do:** `read` / `read_skill` per file with `offset/limit` (e.g. `read SKILL.md --limit 20`, then next chunk only if needed). One file per tool call — lets you stop early.

**Check:** no `cat … | head` / `ls -R` in transcript when `read` can do it; `bash` only for `head` already bounded to ≤20 lines.

---

## 6) Broad-search — `grep -r` without scope

**When:** searching skills, docs, or code for a symbol/pattern.

**Don't:** `grep -r "pattern" ~/stowfiles --include="*.md"` / `grep -R "skill" /opt/.../dist` — lines 15 (63 lines, 7k chars) and 28 (202 lines, 43k chars) scanned `~/.pi`, `~/stowfiles`, `dist` without scope — hits `node_modules`/`dist` noise.

**Do:** `ast_grep_search` (`pattern`, `paths: ["skills/"]`) or `symbol_search` (`query`, `paths`) scoped to `skills/<name>/` or `docs/`. Add `--glob '!dist' --glob '!.pi/agent/sessions'` when `rg` is needed. Prefer scoped tool over `rg` without `paths`.

**Check:** `grep -r` / `find … | xargs grep` only appears with explicit `paths` or `--glob` filter; otherwise `ast_grep_search`/`symbol_search` appears first.

---

## 7) Heredoc prototype loop — `cat > /tmp/*.mjs <<'JS'` × N

**When:** prototyping a parser/injector and running `node /tmp/test_*.mjs`.

**Don't:** `cat > /tmp/test_inject.mjs <<'JS' … JS` + `node …` repeated 4× (lines 52/68/82/92 = 27+29+39+44 lines, 112 total) — each iteration re-dumps heredoc via `bash`.

**Do:** `write /tmp/test_inject.mjs` once, then `bash node /tmp/test_inject.mjs`. Iterate with `edit` (replace range via hash anchors) + `bash node`. One `write`, N `edit`+`node` — no heredoc in `bash`.

**Check:** no `cat > … <<` / `cat <<'EOF'` for temp scripts; temp `.mjs`/`.py` appears as `write` then `bash node`/`bash python`.

---

## 8) Verbose build log — unbounded `tsc`/`pytest` output

**When:** `npx tsc --noEmit`, `pytest`, or `cargo test` for verification.

**Don't:** raw `npx tsc --noEmit` (line 48: 35 lines) without bound — context cost for gate that `lsp_diagnostics` can answer at lower cost. Bounding to `| head -n 30` existing but still oversized vs threshold.

**Do:** pre-check with `lsp_diagnostics` (or `lens_diagnostics`) before `tsc`; if bash needed, cap with `| head -n 20` / `--emit-filtered --keep-head-tail 20`. Keep `bash` for final gate, diagnose via LSP.

**Check:** `npx tsc` / heavy log appears only after `lsp_diagnostics` or with `| head`/`| tail` bound to ≤20 lines, or is post-filtered via `audit.py --emit-filtered`.
