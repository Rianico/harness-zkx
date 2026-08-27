# Information Boundary Pattern

How to split verification and intent between tool and model without leaking implementation detail into the agent's context.

## The Boundary

- **Tool = verification.** Anything the tool can check deterministically (content equality, type, existence, range validity) stays inside the tool. The tool is the authority; the model never supplies the ground truth for the tool's own check.
- **Model = intent.** What to change, why, and what wording to use stays with the model. The tool does not guess intent.
- **Never require the model to re-read or to echo verification data just to keep the tool honest.** If the tool needs data to verify, it resolves it itself from its own store.

## Minimal Handle, Hidden Detail

Expose the smallest stable handle the model can copy (an anchor, short id, or line handle). Hide verbose content, persistence mechanics, and storage layout behind the tool:

- The model copies the handle verbatim.
- The tool resolves the handle, fetches the authoritative content, and verifies before acting.
- Stale or mismatched handles fail closed with a fresh handle — no silent fallback.

This keeps the agent's context lean (a short handle vs. a full dump) and eliminates a class of hallucination where the model invents verification data.

## Grading by Determinism

| Determinism | Owner | Example |
|-------------|-------|---------|
| Hard / checkable | Tool | content match, type, file existence, range validity |
| Soft / qualitative | Model | what to change, phrasing, scope of edit |

When in doubt, ask: *can this be checked without judgment?* If yes, it belongs to the tool.

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
