---
name: programming-expert
description: >-
  Polyglot coding router for Python, TypeScript, Rust, Go, C++, and Bash. Guides implementation, testing, debugging, and refactoring. Use when writing code or scripts, fixing bugs, or resolving compiler and type errors.
arguments: language
argument-hint: |-
  python-expert -- type safety (Pydantic), async, testing, design, observability, resilience, packaging, production
  typescript-expert -- advanced types, Jest, style, tooling, monorepo
  rust-expert -- Cargo, borrow checker, lifetimes, testing
  go-expert -- modules, interfaces, concurrency, table-driven tests
  lua-expert -- tables, metatables, game patterns
  cpp-expert -- CMake, RAII, templates, GoogleTest
  java-expert -- Spring Boot, JPA, Maven/Gradle
  kotlin-expert -- Coroutines, Compose, Ktor, Gradle
  swift-expert -- SwiftUI, concurrency, actors
  php-expert -- Laravel, Eloquent, Pest
  perl-expert -- modern Perl, Moo, security
  bash-expert -- strict mode, quoting, defensive patterns, ShellCheck/Bats/shfmt, portability, templates
  basedpyright-expert -- type checker config, diagnostics, stubs
  omitted -- loads router spine and dispatch table only
metadata:
  manage: [python-expert, typescript-expert, rust-expert, go-expert, lua-expert, cpp-expert, java-expert, kotlin-expert, swift-expert, php-expert, perl-expert, bash-expert, basedpyright-expert]
  depends-on: [skill-authoring]
---

# Programming Expert

Polyglot language router — one description, many projections. The 20% that solves 80%: route by language, then delegate to the focused subskill. Subskills stay hidden from discovery via `managed-by`. The router spends one description instead of 13.

## Principles

General engineering rules applied by every subskill. Language detail varies. The principles hold.

- **Clean commits, clear boundaries** — one commit carries one intent. Use the conventional `feat|fix|doc:` prefix. Keep commits atomic and bisectable. Separate `code` from `docs` from `chore`. Modules own their boundaries. Cross-module calls go through the public contract only.

- **SOLID** — apply at module seams, not per line. Treat SOLID as design pressure, not ceremony.
  - SRP: one reason to change.
  - OCP: open for extension, closed for modification.
  - LSP: substitutability.
  - ISP: narrow interfaces.
  - DIP: depend on abstractions.

- **Clean architecture + deep design — the division of labor.**
  - *Macro-topology (Clean Architecture, Uncle Bob):* draw the line and point dependencies inward. The inner domain knows nothing of outer delivery. Ports and adapters sit at the edges. Use cases orchestrate. Frameworks are plugins. Keep I/O at the boundary with typed admission: Python `BaseModel.model_validate(object→typed)`, TS `zod.parse`, Rust `serde::Deserialize`. Anti-pattern: `model.model_dump().get("x")` loses the types that `model.x` preserves. Isolate business rules from frameworks. Testability comes from decoupling.
  - *Micro-geometry & boundary thickness (Deep Design, John Ousterhout):* keep the interface simple and narrow. Let the inside absorb coordination, caching (LRU), atomic transactions, and invariant enforcement. Explicitly reject **"Classitis"** — 15 shallow 5-line classes, DTOs, and mappers to do one basic task.
  - *Systems engineering exemplars:*
    - **Unix:** the file descriptor (`open`, `read`, `write`, `close`) hides filesystems, sockets, and pipes behind one integer handle.
    - **SQLite:** a 6-function C API and one amalgamation file (`sqlite3.c`) hide 150k lines of internals. The hidden machinery: ACID B-trees, WAL, and a bytecode VM. The API surface is `open`, `prepare_v2`, `step`, `column`, `finalize`, `close`.
    - **Linux kernel (Linus Torvalds):** keeps cohesive functions whole. Uses deep function-pointer tables (`struct file_operations`) over deep OOP inheritance hierarchies.

- **Design deepening vs. scope creep** — distinguish internal structural refactoring from unmandated scope expansion.
  - *Harmful scope creep (`P2`):* unmandated public APIs, mutating payload schemas, unrequested user-visible parameters, altering repo tooling or configs (`.config/wt.toml`, CI workflows, linter configs).
  - *Permitted design deepening:* submodule decomposition that cures code smells (Divergent Change, God files, Shotgun Surgery), extracting cohesive internal helpers, adding architectural regression tests (`test/arch/`). Deepening cures smells and strengthens invariants without widening public surfaces. Reviewers treat internal deepening as in-scope work.

- **Domain & boundaries** — decide what belongs in the core domain and what belongs at the edges. Name the boundaries that must stay stable as the system evolves. Use bounded contexts, ubiquitous language, and aggregate invariants. Align code structure with domain concepts. Keep each table inside one context. Enforce the ubiquitous language: canonical domain terms and avoided synonyms (`GLOSSARY.md`) are load-bearing boundaries. A banned synonym in a type, parameter, error message, or comment is domain boundary drift.

- **Transactions & coupling** — decide what must commit together and what runs async. Name each new coupling and judge whether it is acceptable.
  - Multi-step mutations spanning multiple records or tables run in one atomic transaction (`BEGIN IMMEDIATE`). Fragmenting them is a defect.
  - Hybrid disk+DB operations surface desync warnings or errors explicitly. A silent console log hides the desync.
  - Modify one aggregate per transaction.
  - Prefer events, Saga, or Outbox over 2PC.
  - Batches return `BatchResult{ok, failed}`. One failed item aborts nothing.
  - Jobs move `pending→running→succeeded|failed` with idempotent, at-least-once handlers.

- **Operational realism** — ask what operational burden each decision creates. Ask what becomes easier and what becomes harder afterwards. Prefer operable, observable, independently deployable boundaries. Split microservices only after the pain is real. Emit JSON structured logs with `correlation_id` (`ContextVar`/`AsyncLocalStorage`) plus `method/path/status`. Keep Prometheus label cardinality bounded — a `user_id` label explodes it. Watch golden signals: latency, traffic, errors, saturation.

- **Configuration — fail fast** — externalize env-specific values. Parse and validate all config at boot into typed `Settings` (Py `BaseSettings`/`Field(alias=)`, TS `zod` env schema, Rust `config` crate). Crash with field-level errors before serving. Keep secrets out of code, logs, and errors.

- **Resilience — retry only transient faults** — retry `ConnectionError`/`TimeoutError` and `429/502/503/504`. Treat `ValueError`, `TypeError`, and auth 4xx as permanent failures. Use `wait_exponential_jitter` with a cap on attempts *and* wall time. Jitter prevents the thundering herd.

- **Resources — RAII & signal-safe cleanup** — acquire in `enter`/`aenter`. Release unconditionally in `exit`/`aexit` (`with`/`using`/`defer`/`Drop`/`trap ... EXIT`). Stack cleanups with `ExitStack`/`AsyncExitStack`. Finalize streams in `finally`/`exit`. Cleanup runs on every exit — signals, exceptions, interrupts, crashes. The same invariant governs temp files, locks, descriptors, and processes. Test-scoped environment and platform mutations must capture and restore in one construct (fixtures, `afterEach`, RAII, `vi.stubEnv`, `jest.replaceProperty`, `monkeypatch`). Restore original values for pre-existing keys, and use `delete process.env.KEY` on teardown only for keys added during the test — in Node.js, assigning `undefined` sets the string `'undefined'`.

- **Strict by default — permissive hides bugs** — silent empty results, swallowed pipe errors, and implicit `any` hide defects. Separate declaration from assignment when assignment can fail (`local x; x=$(cmd)`, `export x; x=$(cmd)`). Declaration builtins return 0 and mask the exit status under `set -e`. Enable the strictest checks first (`strict`/`--enable=all`/`-Wall -Werror`/type `strict`). Relax only with a narrow, reasoned suppression at the smallest scope.

- **Data is not code — keep channels separate** — put data in typed data channels. Use parameterized queries, placeholders, typed args, and arrays for transport. Interpolating data into code via strings opens SQL injection, XSS, and command injection. Terminate options with `--` before untrusted positional args (`cmd -- "$arg"`). Building commands or code by string concatenation is banned. Avoid `eval` and string-concat execution.

- **Delimiters lie — use structured over ad-hoc split** — ad-hoc splitting (`split(',')`, newline/token) fails when the data contains the delimiter. Choose delimiters that cannot appear in the data, or use structured encodings (arrays, JSON, length-prefix). If you must split, prove the delimiter is safe first.

- **Platform is a dependency — probe, don't assume** — the same API differs across platforms and versions. Declare the minimum version. Probe capabilities and feature-detect. Gate with a fallback. Fail fast with an actionable message (`install X >=Y`). Test on the targets. When investigating test flakiness, isolate the case first: passing alone but failing in the file indicates leaked cross-test state (polluted globals or platform stubs), not external environment.

- **Mechanical population verification — derive populations mechanically** — never verify a set you enumerated. Derive the full population via mechanical tools (`tsc`, `basedpyright`, token-anchored `rg '\bIDENT\b'` or `rg -w IDENT`, LSP references, full test suite on dynamic boundaries like string keys, reflection, serialization schemas, config keys, i18n, docs). Hand-enumerating items allows unlisted defects to escape. This single invariant governs module mock surfaces (spread unmocked exports), rename sweeps, and ratchet re-pins.

- **Artifacts: ADR / Blueprint / Technical standards** — three durable artifacts anchor each decision.
  - The ADR is the concise decision log: context → decision → consequences, plus rejected alternatives.
  - The blueprint is the current model: components, boundaries, interfaces, data/control flow, runtime shape, invariants, risks.
  - Technical standards are the reusable rules: naming, layering, dependency direction, FK/deletion policy, API contracts.
  - Update the blueprint or standards only for a reusable paradigm. One-off details stay out.

- **Decision framing** — keep reasoning decision-oriented. Surface trade-offs explicitly. Make rejected alternatives concrete. Tie each concern back to boundaries, invariants, and risks.

- **Refutation by counterexample & oracle tests** — refute defects with concrete evidence.
  - When diagnosing an invariant violation or algorithmic failure, produce a minimal failing input (`input -> expected vs observed`).
  - Cosmetic heuristic tweaks prove nothing.
  - For non-trivial state machines, combinatorial engines, and pairing algorithms, write minimal exhaustive small-input oracle tests or property-based tests.
  - Prove the invariants before optimizing.

- **Self-described code** — names reveal intent. Functions do one thing. Errors fail loud with context. Comments explain why, not what. `object` forces validation. `Any` silences the checker. Reserve `Any` for truly dynamic data or designated transport/IPC zones (file-level suppression only). Validate once at admission. Trust the data inside.

## Dispatch

Read `$SKILL_DIR/subskills/<name>/SKILL.md` for the language you need. Use `Read`, because `managed-by` hides subskills from the `Skill` tool.

| Subskill                                                        | Load when                                                                                                                       |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| [python-expert](subskills/python-expert/SKILL.md)               | type safety (Pydantic strict), async, testing, design, observability, resilience, resources, jobs, packaging, production         |
| [typescript-expert](subskills/typescript-expert/SKILL.md)       | advanced types, Jest, style, tooling, monorepo                                                                                  |
| [rust-expert](subskills/rust-expert/SKILL.md)                   | Cargo, borrow checker, lifetimes, Result, async                                                                                 |
| [go-expert](subskills/go-expert/SKILL.md)                       | modules, interfaces, goroutines, table-driven tests                                                                            |
| [lua-expert](subskills/lua-expert/SKILL.md)                     | tables, metatables, game loops, Love2D                                                                                          |
| [cpp-expert](subskills/cpp-expert/SKILL.md)                     | CMake, RAII, templates, GoogleTest                                                                                              |
| [java-expert](subskills/java-expert/SKILL.md)                   | Spring Boot, JPA, Maven/Gradle, JUnit                                                                                           |
| [kotlin-expert](subskills/kotlin-expert/SKILL.md)               | Coroutines/Flow, Compose, Ktor, Gradle                                                                                          |
| [swift-expert](subskills/swift-expert/SKILL.md)                 | SwiftUI, actors, Sendable, strict concurrency                                                                                   |
| [php-expert](subskills/php-expert/SKILL.md)                     | Laravel, Eloquent, Pest, auth/policies                                                                                          |
| [perl-expert](subskills/perl-expert/SKILL.md)                   | modern Perl 5.36+, Moo, taint, Test2                                                                                            |
| [bash-expert](subskills/bash-expert/SKILL.md)                   | defensive Bash, strict mode, quoting, file/temp safety, args, portability, ShellCheck/Bats                                      |
| [basedpyright-expert](subskills/basedpyright-expert/SKILL.md)   | pyright config, diagnostics, stubs, migration                                                                                   |

An omitted argument loads only the spine above. For an unknown language, use the closest subskill or escalate. Do not invent a new projection in place.

## When to Use vs Neighbors

- **This router:** language-idiomatic implementation, debugging, testing, review. It applies the principles above within each language.
- **`adr`:** owns the ADR lifecycle and the full decision log process. This router owns the architecture foundations (boundaries, trade-offs, DDD) and the lightweight ADR principle.
- **`sysops-expert` / `safety-guard`:** ops, security, privacy — not code style.
- **`basedpyright-expert` vs `tdd-expert`:** type checker config lives here. Test strategy lives in `tdd-expert`.

## Migration

**Status: Complete.** The router manages 13 subskills: 12 language experts plus `basedpyright-expert`. Legacy top-level `skills/*-expert` directories are retired. Subskills are canonical.

Adding a new language: create `$SKILL_DIR/subskills/<new>-expert/SKILL.md` with `name: <new>-expert` and `managed-by: programming-expert`. Append it to `manage`. Run `validate-deps.py check`, `lint`, and `context-check`.

## Verification

Each subskill declares its deterministic gate. The router passes when the dispatched subskill's gate passes:

```bash
uv run ruff check . && uv run basedpyright && uv run pytest          # python
npx tsc --noEmit && npm test                                           # typescript
cargo check && cargo test && cargo clippy                              # rust
go vet ./... && go test ./...                                          # go
luacheck . && busted                                                   # lua (when present)
shellcheck --enable=all --external-sources **/*.sh && shfmt -i 2 -ci -bn -sr -kp -d . && bats tests/  # bash
```

See the subskill for the exact command.

## References

- Sources: `$SKILL_DIR/subskills/<language>-expert/` — each subskill is self-contained with its `references/` and `scripts/`.
- Authoring: the `skill-authoring` skill under `ai-engineering-expert`.
