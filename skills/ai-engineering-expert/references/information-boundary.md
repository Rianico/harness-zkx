# Information Boundary Pattern: Formal Substrate vs. Semantic Reasoner

How to split mechanical verification and probabilistic intent without leaking implementation details or state into the agent's context.

## The Boundary

- **Formal Substrate = Environmental Verification & Mechanical Guarantees.** Anything checkable deterministically (type safety, AST validity, content equality, database integrity, range limits, test suites) stays inside the formal substrate. The substrate is the supreme authority; the reasoner never supplies the ground truth for the substrate's own check.
- **Semantic Reasoner = Intent, Synthesis & Disambiguation.** What to change, why, how to align with user goals, and how to resolve semantic conflicts stays with the model. The formal substrate does not guess intent.
- **Never require the reasoner to re-read or echo verification data just to keep the substrate honest.** If the substrate needs data to verify, it resolves it directly from its own store or environment.

## Minimal Handle, Hidden Detail

Expose the smallest stable handle the model can copy (an anchor, short id, or line handle). Hide verbose content, persistence mechanics, AST nodes, and storage layout behind the tool:

- The model copies the handle verbatim.
- The substrate resolves the handle, fetches the authoritative content, and verifies before acting.
- Stale or mismatched handles fail closed with a fresh handle — no silent fallback.

This keeps the agent's context lean (a short handle vs. a full dump) and eliminates a class of hallucination where the model invents verification data.

## Grading by Determinism

| Determinism        | Owner | Examples |
| ------------------ | ----- | -------- |
| Hard / checkable   | **Formal Substrate** (Compilers, DBs, Linters, CI, AST) | Content match, type checks, schema invariants, file existence, git merges |
| Soft / qualitative | **Semantic Reasoner** (LLMs, Evaluators) | Intent synthesis, trade-off analysis, phrasing, semantic conflict resolution |


When in doubt, ask: _can this be checked without judgment?_ If yes, it belongs to the tool.

## Tool Owns Bytes — Deterministic Generation

For byte-identical artifacts, the tool is source of truth: it embeds templates in `scripts/*.py`, emits via `--dry-run` diff and writes + `WARNING` on stderr for mixed deterministic+semantic files (model proofreads only warned sections). Expose minimal handles/flags (`--flavor`, `--with-coverage`), hide storage layout. Reference scaffold: `skills/scaffold/scripts/scaffold.py` owns `.releaserc.json`/`pyproject.toml`/`release.yml` bytes — template dumps in `references/` are duplicate truth (One Truth, Many Projections). Anti-pattern: model hand-copying templates from references — stale by construction.

## Illustrative Instantiation — Hash-Anchored Edit (pi-better-edit)

> [!example] Concrete example — not the pattern itself
> In `pi-better-edit`, `read` returns lines as `anchor│content` (e.g. `aB3│  const x = 1`). The three-character anchor is the handle; the content after `│` is for human reading. `edit` takes bare anchors (`remove_from`, `remove_to`) and bare content (`replacement_text` without `anchor│` prefixes). The tool resolves each anchor to its current line, verifies the range is still valid, and applies the change. The hash content is a reference example behind this pointer — the spine ([SKILL.md](../SKILL.md)) never embeds it inline.

For a live example of the content behind the pointer, see the hashline contract in that repo's `CONTEXT.md` / `docs/` — the reference here is the pointer, not the inline mechanism.

## When to Use

- Any tool that reads then writes (edit, patch, migration) where stale reads cause silent corruption.
- Anywhere the model would otherwise be tempted to re-supply file content to "prove" it read correctly.

## Anti-Patterns

- **Echo verification:** requiring the model to paste file content back to authorize an edit.
- **Handle + content coupling:** putting the handle inside the editable content so the model must preserve it.
- **Verbose handles:** handles that carry the full content and bloat context — defeats the purpose.
