# Development Patterns

Portable code and type conventions. Consult on every change that touches state, boundaries, surfaces, or verification.

## 1. Spine — State, Boundaries, Surfaces

**Immutable state** — new values from inputs; origins read-only. `updated = evolve(original, patch)` over mutation. Mutation stays at owning boundary with recovery.
_Check:_ no function mutates caller-owned object; tests assert `original` unchanged.

**Typed boundaries** — validate once at admission, trust inside.

- **Admission:** API/message/file/config — schema (Pydantic/Zod/serde), reject invalid.
- **Inside:** trust typed model; no `Any`/`object`/`dict.get` fallbacks.
- **Emission:** serialize (`model_dump`/`toJSON`) only at transport/IPC/file/API. Logic stays typed.

```python
# trust typed model — preferred
for name, conf in config.languages.items(): ...
# loses type — move to boundary
data = config.model_dump(); langs = data.get("languages")
```

When narrowing tangles, ask: why does this serialization exist here? Move it to the boundary. Prefer TypeScript over JS, Pydantic over `object`/`Any`.

**Graded surfaces** — narrowest promise that satisfies use.

- Cross-module → public contract (needs cutover plan).
- Internal → private; don't widen to silence warning — move caller or seam.
- Deprecation → internal-only: remove + update callers atomically (no deprecated mark). Public/cross-boundary: deprecate with shim + migration window, cutover plan before removal.
  SOLID at module seams, not per-line.

## 2. Guards — Errors, Security, Suppressions

**Errors fail loud** — every path has explicit branch: handle, map to typed error, or propagate. Log cause, no secrets. Fail-fast at invariant boundary.
_Check:_ no empty `except`/`catch`; every catch re-raises, returns `Result`/`Err`, or logs with context.

**Security — negative path designed**

- Secrets from env/secret manager, never in code/logs/errors.
- Validate inputs at admission; auth/rate-limit/injection/XSS/CSRF at owning boundary.
- On finding: stop → `security-reviewer` agent, fix CRITICAL first, rotate exposed secret. Classify reversible/compensable/irreversible.

**Suppressions — shrink-only, smallest seam** — fix code first; when suppression is right, scope narrowly and document why.
Ladder: 1 Fix code → 2 line `ignore` + reason → 3 file suppression + reason → 4 targeted config (one category, 50+ hits) → 5 project-level (drift signal, needs authority + review trigger) → 6 global disable (boundary decision, authority + invariant + removal condition).

```python
# <tool>: ignore[<rule>]
# Reason: <why legitimate, what invariant still holds>
```

_Guard rule:_ baselines shrink-only. Growth needs authority, narrow scope, owner, review trigger. Moving code outside guard scope is a boundary change.

## 3. Runtime and Verification

**Declared runtimes** — native tool that owns version+deps; commit version file.

- Single: `uv`+`.python-version` (default 3.14), `cargo`+`rust-toolchain.toml`, `corepack`/`nvm`+`.nvmrc`.
- Multi (2+ runtimes): `asdf`+`.tool-versions`; `asdf install` syncs all.

**Verification closes the loop** — evidence, not stale green. Restart daemon after type/config changes; clean-build after refactors; clear test cache when stale; benchmark real path before performance claims.
_Check:_ re-run failing signal from fresh state and confirm terminal invariant.

## 4. Context — Keep Lean

Dispatch when main only needs result: research → conclusions; sub-module → report+files; pipeline (`tdd→refactor→verify`) → one subagent per stage. Handoff via file pointer + dumped artifact, not bulk paste.

Subagents share same worktree — parallel writers race. Fan-out ≥2 touching `src`/`test`/tracked files → isolate with `worktree`. Pattern: main creates one worktree per task; dispatch `subagent` with that `cwd` + branch instruction; isolated writes; verify each worktree; integrate; clean up. Single writer or read-only → no worktree. See `git-convention.md` + `branch-worktree-pr` skill.

**Sub-skills — match, don't wait** — router parents stay lean; model Reads the matching sub-skill as soon as the task matches its triggers. Explicit $domain is one trigger, task-match is the other — never wait for the user to name the domain. Creating/editing any agent-consumed doc always loads writing-for-agents.
_Check:_ task matched a sub-skill trigger means its file was Read before acting.

## Ephemeral artifacts → `.lsz/tmp`

Route scratch/repro through `.lsz/tmp` (gitignored). `mkdir -p .lsz/tmp`; `python -c "..." > .lsz/tmp/repro.json`. Keep root and `tests/` clean.
_Check:_ `git status` shows no untracked temp outside `.lsz/tmp`.
