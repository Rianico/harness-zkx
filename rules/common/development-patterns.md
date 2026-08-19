# Development Patterns

Portable code and type conventions. Consult on every change that touches state, boundaries, surfaces, or verification.

## 1. Spine — State, Boundaries, Surfaces

### Immutable state

Create new values from inputs; treat origins as read-only. Prefer pure functions that return updated copies (`updated = evolve(original, patch)`) over in-place mutation. Mutation narrows to the owning boundary that declares it and owns recovery.

_Check:_ no function mutates a caller-owned object; tests assert `original` unchanged after the call.

### Typed boundaries

Validate once at admission, trust types inside.

- **Admission (input boundary):** API endpoints, message handlers, file parsers, config loaders — validate with a typed schema (Pydantic, Zod, serde) and reject invalid data there.
- **Inside:** trust the typed model. Avoid repeated defensive checks and ad-hoc `Any`/`object`/`dict.get` fallbacks.
- **Emission (output boundary):** serialize (`model_dump()`, `toJSON()`) only at transport, IPC, file writers, and API responses. Application logic stays on typed models.

```python
# stays typed — preferred
for name, conf in config.languages.items():
    ...

# loses type — move to boundary or remove
data = config.model_dump(); langs = data.get("languages")
```

When type narrowing feels tangled, ask: why does this serialization exist here? Move it to the boundary.

Prefer type-safe libraries that shift errors to build/validation time: TypeScript over plain JS for frontend, Pydantic over `object`/`Any` for Python models.

### Graded surfaces

Grade every exported surface by the promise it carries. Choose the narrowest visibility that satisfies actual use.

- Used across modules → make public and treat as contract (needs compatibility/cutover plan to change).
- Truly internal → keep private and enforce encapsulation; do not widen to silence a warning — move the caller or the surface to the correct seam.

Apply SOLID at module seams (single responsibility per module, depend on seam abstractions) — not as a per-line incantation.

## 2. Guards — Errors, Security, Suppressions

### Errors fail loud

Every error path has an explicit branch: handle, map to a typed error, or propagate. Log or surface the cause; keep sensitive data out of messages. Prefer fail-fast at the boundary where the invariant is known.

_Check:_ no empty `except`/`catch`; every catch either re-raises, returns `Result`/`Err`, or logs with context.

### Security — negative path designed

- Read secrets from environment or secret manager; keep them out of code, logs, and error payloads.
- Validate all inputs at admission; enforce auth, rate limits, and injection/XSS/CSRF controls at the boundary that owns the effect.
- On finding an issue: stop, use the `security-reviewer` agent, fix CRITICAL first, rotate any exposed secret. Classify effects as reversible / compensable / irreversible and scale controls accordingly.

### Suppressions — shrink-only, scoped to the smallest seam

Fix the code first. When suppression is the right call, scope it as narrowly as possible and document why.

**Scope ladder (most to least precise):**

1. Fix the code — preferred
2. Line-level `ignore` with reason — single instance
3. File-level suppression with reason — pattern confined to one file
4. Targeted config (e.g., `allowedUntypedLibraries` for internal packages) — one category, 50+ hits
5. Project-level disable — signals architectural drift; record authority and review trigger
6. Global rule disable — boundary decision only; record authority, invariant preserved, and removal condition

Document every suppression at the suppression site:

```python
# <tool>: ignore[<rule>]
# Reason: <one-line why this is legitimate and what invariant still holds>
```

_Guard rule:_ baselines shrink-only. Growth needs decision authority, narrow scope, owner, and a review trigger. Moving code outside a guard's scope is a boundary change.

## 3. Runtime and Verification

### Declared runtimes

Use the language-native tool that owns version + deps; commit the version file.

- **Single-language:** `uv` + `.python-version` for Python (default 3.14 for new projects), `cargo` + `rust-toolchain.toml` for Rust, `corepack`/`nvm` + `.nvmrc` for Node. Native tooling gives faster, idiomatic integration.
- **Multi-language (2+ active runtimes, e.g., Python + Node):** `asdf` + committed `.tool-versions`; `asdf install` syncs all. Other tools (including `uv`) respect `.tool-versions` when present.

### Verification closes the loop

Every fix ends with evidence of closure, not just a green run on a stale cache.

- Restart/refresh the daemon after type or config changes.
- Clean-build after significant refactors.
- Clear test cache when results look stale.
- Attach numbers to any performance claim — benchmark on the real path before stating it.

_Check:_ after a fix, re-run the failing signal (typecheck / tests / repro) from a fresh state and confirm the terminal invariant holds.

## 4. Context — Keep Lean

Dispatch subtasks to subagents and keep the main session lean. When the main agent only needs the result, delegate:

1. Research → subagent returns conclusions.
2. Sub-module implementation → subagent returns a report + changed files.
3. Staged pipeline (`tdd → refactor → verify`) → one subagent per stage.

Hand off across context gaps (agent↔subagent, compaction) by file pointer + dumped artifact, not by pasting bulk content into context. The pointer names the material and the branches that trigger loading it.

### Ephemeral artifacts → `.lsz/tmp`

Route temporary files, scratch outputs, and ad-hoc repros through `.lsz/tmp/` (gitignored). Keep the repo root and `tests/` clean — `tests/` holds only committed, reviewable tests.

- Create on demand: `mkdir -p .lsz/tmp` before writing.
- Example: `python -c "..." > .lsz/tmp/repro.json`, `pytest --tmp-path=.lsz/tmp/…`.

_Check:_ `git status` shows no untracked temp files outside `.lsz/tmp`; transient artifacts do not survive review.
