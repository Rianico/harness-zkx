# Information Boundary Pattern: Formal Substrate vs. Semantic Reasoner

How to split mechanical verification and probabilistic intent without leaking implementation details or state into the agent's context.

## The Boundary

- **Formal Substrate = Environmental Verification & Mechanical Guarantees.** Anything checkable deterministically (type safety, AST validity, content equality, database integrity, range limits, test suites) stays inside the formal substrate. The substrate is the supreme authority. The reasoner never supplies ground truth for the substrate's check.
- **Semantic Reasoner = Intent, Synthesis & Disambiguation.** The model decides what to change and why. It aligns the work with user goals. It resolves semantic conflicts. The formal substrate does not guess intent.
- **Never require the reasoner to re-read or echo verification data.** The substrate resolves it from its own environment.

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

The tool owns byte-identical artifacts. It embeds templates in `scripts/*.py` and emits preview diffs. The model reviews only warned sections. Expose minimal handles/flags (`--flavor`, `--with-coverage`), hide storage layout. A deterministic generator owns template bytes in `scripts/`. Template dumps in `references/` are duplicate truth (One Truth, Many Projections). Anti-pattern: model hand-copying templates from references — stale by construction.

## Illustrative Instantiation — Hash-Anchored Edit

> [!example] Concrete example — not the pattern itself
> The reader returns `anchor│content` rows (for example `aB3│  const x = 1`). The short opaque anchor is the handle, and the agent copies it verbatim. Content after `│` is for human reading only. The writer takes bare anchors (`remove_from`, `remove_to`) and bare replacement content. It never takes the prefixed form. The tool resolves each anchor, verifies the range is still valid, then applies the change.

The reference here is the pointer, not the inline mechanism.

## When to Use

- Any tool that reads then writes (edit, patch, migration) where stale reads cause silent corruption.
- Anywhere the model would otherwise be tempted to re-supply file content to "prove" it read correctly.

## Anti-Patterns

- **Echo verification:** requiring the model to paste file content back to authorize an edit.
- **Handle + content coupling:** putting the handle inside the editable content so the model must preserve it.
- **Verbose handles:** handles that carry the full content and bloat context — defeats the purpose.
