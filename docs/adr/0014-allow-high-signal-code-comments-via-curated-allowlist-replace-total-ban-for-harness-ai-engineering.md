# 14. Allow high-signal code comments via curated allowlist — replace total ban for harness AI engineering

Date: 2026-09-02

## Status

Accepted — grilling Q1–Q7 reached shared understanding 2026-09-02. Implements LSZ `Respect Tool Feedback` + `Artifact Hygiene` + `Provenance`.

## Context

`pi-better-edit` failed CI on `custom/no-comments: error` — `Comments are not allowed. The code must be self-documenting` — while landing `feat/arch-deepening-all` (6 deep modules: `EditTool`+`TuiPresenter`, `ServedSession` epoch/tombstone, `HealingPolicy` ordering `orphan→single→boundary`, `Drift` `editedIntervals`/`deltaBefore`, `PayloadContract` hoisted path, `EditPresentation`). The rule is `eslint.config.js` `Program()` `sourceCode.getAllComments()` with allowlist `SAFETY:` + `Given|When|Then` + `if (filename.includes("edit-pipeline")) return;` and 16 globs `files:off` (`mutation-engine/**`, `hashline/served*`, `file-content/**` …) + `test/** off`. `// eslint-disable` self-fails — only config-scope `files:off` escapes.

Research (3 subagents, `.lsz/tmp/research-comments-*.md`) found no high-trust source supports a total ban. Clean Code Ch.4, Code Complete, Google guides converge on *self-documenting first, comments for `why`* (invariants, warnings, regex/encoding, hacks, copy URL, ADR/bug links, `TODO(#)`). Wallace et al., *Empirical SE* Springer 2025 (eye-tracking, n=20): comments moved correctness **-30% to +34% per snippet**, up to 23% of fixations — quality > quantity. For models, ~38% comment density → **+40% HumanEval, +54% MBPP** vs 0% (Song et al., ACL Findings 2024); stripping `why/invariant/seam/ADR` hurts intent tasks **-90% to +67%** (Imani et al., ICSE 2026 CAV; Anthropic *Effective Context Engineering*). The 16 exempted globs are exactly where `CONTEXT.md` invariants live (`tombstone`, `epoch`, `strict vs pos-free`, `served span`, `pure edit`), conceding the ban fails where it matters.

Harness `everything-claude-code` scaffolds this rule into every repo via `skills/scaffold` and enforces it via `wt.toml [pre-merge].gate` → `eslint`. `CONTEXT.md` is `LSZ` (Skill/Agent/Orchestration/Manifest/Provenance) — no comment policy ADR exists (0001–0013 silent), so the scaffold ships an undocumented `forbid all`. `pi-better-edit` is the first consumer where the ban was falsified at a load-bearing seam. The choice is patch `pi-better-edit` alone (grow globs to 17) vs decide harness-wide (ADR 0014, template+gate, shrink globs).

## Decision

We will replace `forbid all` with a **curated, closed allowlist** — deterministic CI gate + semantic guideline split — harness-owned, shrink-only.

**1. Closed allowlist — CI gate (deterministic, `error`-level).** `custom/no-comments` allowlist regex:

```
SAFETY:|WHY:|Invariant:|See ADR-|via https://|TODO\(#\d+\):|HACK:|GHERKIN
```

where `GHERKIN = ^\s*(Given|When|Then|And|But|Feature|Scenario|Background|Scenario Outline|Examples)\b/i` (existing) and legal `/**` header remains separate. `WHY|Invariant|See ADR-` must cite a checkable provenance (test, ADR number, or URL) — `// why: trust me` stays `error`. Everything else (`// increment`, `// ====`, commented-out code, journal/byline, per-function boilerplate) stays `error`. `if (filename.includes("edit-pipeline")) return;` is deleted — those 35 phase-diagram lines become `// WHY:`/`// See ADR-` like everyone else.

**2. Semantic guideline — rule (LLM-facing, not CI).** Guideline lives in `~/.pi/agent/rules/common/development-patterns.md` (not `writing-for-agents`), extending `Suppressions — shrink-only, smallest seam` and `Graded surfaces`. Text: *prefer extraction/rename until code explains `what/how`; when code cannot carry `why` (invariant, warning, unidiomatic check, regex, hack, copy URL, ADR link, bug ID), use allowlist tag with link/test; otherwise extract.* Cross-link from `ai-engineering-expert` 80/20 spine per `argument-hint` router.

**3. Escape hatch — `files:off` only, shrink-only.** `// eslint-disable-next-line custom/no-comments` remains flagged by design — no line-level escape. Only `files: ["..."] → "custom/no-comments":"off"` with `reason+owner+review trigger` is allowed, ladder entry 4 `targeted config (one category, 50+ hits)` → 5 `project-level (drift signal, authority+review)` per `development-patterns.md §2` / Keel §6. The 16 globs are **deprecated, shrink-only, no new `off` without ADR**; each later retrofit deletes one glob and adds tags. `test/** off` stays.

**4. Ownership — harness owns regex.** `harness/everything-claude-code` `scaffold` template renders `eslint.config.js` verbatim; `pi-better-edit/eslint.config.js` is *generated* (mark `generated — do not hand-edit, run scaffold`). Per-project extension is via `files:off` with ADR uplift, not local regex fork — `one adapter = hypothetical seam, two = real`.

**5. Verification — `C-gate-only`.** Committed gate is `wt.toml [pre-merge].gate` → `npm run typecheck && npm test && npx commitlint … && eslint` staying green. Human (`time-to-approve` + stale-comment defects) and model (`pass@k` on hashline tasks, CAV) are *future work* in `harness/docs/research/comments-in-harness-ai-engineering.md`, not CI — per `ai-engineering-expert` `eval-first` but staged.

## Consequences

**Scaffold + template:** `skills/scaffold/subskills/git/SKILL.md` note updated (`custom/no-comments` allowlist), `scaffold` renders new `eslint.config.js` (allowlist regex, no `edit-pipeline` hard-code, 16 globs marked deprecated). New repos no longer need `files:off` for invariants — `allowlist` covers them. Migration docs note `generated` flag.

**Quality gate:** `commands/quality-gate.md` teaches `fix code → recast to allowlist → file off with reason` per ladder. `wt.toml` gate unchanged — regex change is the gate. No `line disable` carve-out — preserves `fix code first`.

**Backport:** `pi-better-edit` first consumer — `feat/arch-deepening-all` PR #64 retrofits `// Invariant:`, `// WHY:`, `// See ADR-` tags and shrinks a few globs (e.g., `src/edit.ts`, `src/hashline/healing/**` after `HealingPolicy`). `src/edit-pipeline.ts` exception deleted. `pi-session-*.html` remains untracked.

**Easier:** High-signal comments (`tombstone ∪ epoch → pos-free`, `healing ordering`, `deltaBefore`) stay with code, reducing re-introduction of ADR-0005/0008/0013 bugs; model retrieval on `why` improves; review can cite `See ADR-0013` instead of re-explaining. `files:off` growth stops.

**Harder:** 7-tag regex is still coarse — `// WHY:` without provenance will be `error` until tag is refined; initial retrofit touches ~16 files. Legal `/**` docs need a separate `eslint` rule to avoid conflating with the allowlist. Training still benefits from comment density, but inference token cost rises slightly.

**Risks & mitigations:** Allowlist drifts to `.*` → mitigate: harness ADR is single writer, `pi-better-edit` diff is the first shrink; `validate-deps.py context-check` can lint `eslint.config.js` against ADR allowlist. `TODO(#\d+):` without tracker → mitigate: require digits (already in regex). `development-patterns.md` guideline could bloat `Metadata Cost` → mitigate: keep to one paragraph + 3 good/bad examples, no new skill.

