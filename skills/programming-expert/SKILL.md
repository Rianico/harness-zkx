---
name: programming-expert
description: >-
  Foundational coding principles and polyglot expertise across languages. Use when writing, reviewing, or hardening code, enforcing Clean Code/SOLID principles, or resolving architecture issues.
arguments: language
argument-hint: |-
  python-expert -- type safety (Pydantic), async, testing, design, observability, resilience, packaging, production — 18 sub-domains
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
---

# Programming Expert

Polyglot language router — one description, many projections. The 20% that solves 80%: route by language, then delegate to the focused subskill. Subskills are hidden from discovery (`managed-by`) so context cost drops from ~3250 chars (13 descriptions) to ~280 chars (one router).

## Principles

General engineering rules applied by every subskill — language detail varies, principles don't.

- **Clean commits, clear boundaries** — one commit = one intent, conventional `feat|fix|doc:` prefix, atomic bisectable; separate `code` vs `docs` vs `chore`; modules own their boundaries, cross-module only via public contract, no hidden coupling.
- **SOLID** — SRP one reason to change, OCP open for extension closed for modification, LSP substitutability, ISP narrow interfaces, DIP depend on abstractions; apply at module seams, not per-line; SOLID as design pressure, not ceremony.
- **Clean architecture** — dependency rule: inner domain knows nothing of outer delivery; ports & adapters at edges, use cases orchestrate, frameworks are plugins; keep I/O at the boundary, typed admission there — Python `BaseModel.model_validate(object→typed)` / TS `zod.parse` / Rust `serde::Deserialize`. Anti-pattern: `model.model_dump().get("x")` loses types that `model.x` preserves. Ask: which code is policy vs detail? Are inner layers protected from frameworks? Is abstraction serving a real boundary vs speculative purity? Isolate business rules from frameworks; testability through decoupling.
- **Domain & boundaries** — what belongs in core domain vs edges; what boundaries must stay stable as system evolves; bounded contexts, ubiquitous language, aggregate invariants; align code structure with domain concepts, don't share tables across contexts.
- **Transactional & coupling** — what must be transactional together vs asynchronous; what coupling is introduced and is it acceptable; avoid modifying two aggregates in one transaction; prefer events/Saga/Outbox over 2PC; batches return `BatchResult{ok, failed}` never abort on one item; jobs are `pending→running→succeeded|failed` with idempotent, at-least-once handlers.
- **Operational realism** — what operational burden does the decision create; what becomes easier vs harder afterwards; prefer operable, observable, independently deployable boundaries; avoid premature microservice splits; emit JSON structured logs with `correlation_id` (`ContextVar`/`AsyncLocalStorage`) + `method/path/status`; Prometheus bounded cardinality (never `user_id` label); watch golden signals (latency/traffic/errors/saturation).
- **Configuration — fail fast** — externalize env-specific values; parse and validate all config at boot into typed `Settings` (Py `BaseSettings`/`Field(alias=)` / TS `zod` env schema / Rust `config` crate); crash with field-level errors before serving. No secrets in code/logs/errors.
- **Resilience — retry only transient** — retry `ConnectionError/TimeoutError` + `429/502/503/504`, never `ValueError/TypeError`/auth 4xx; `wait_exponential_jitter` with cap on attempts _and_ wall time; jitter to avoid thundering herd.
- **Resources — RAII & signal-safe cleanup** — acquire in `enter`/`aenter`, release unconditionally in `exit`/`aexit` (`with`/`using`/`defer`/`Drop` / `trap ... EXIT`); stack with `ExitStack`/`AsyncExitStack`; streaming finalizes in `finally`/`exit`. Ensure cleanup runs on all exits (signals/exceptions/interrupts/crashes), not just happy path — same invariant for temp files, locks, descriptors, processes.
- **Strict by default — permissive hides bugs** — permissive defaults mask failures (silent empty, swallowed pipe errors, implicit `any`). Separate declaration from assignment when assignment can fail (`local x; x=$(cmd)`, `export x; x=$(cmd)`) to prevent declaration builtins returning 0 from masking exit status under `set -e`. Enable strictest checks first (`strict`/`--enable=all`/`-Wall -Werror`/type `strict`); relax only with narrow, reasoned suppression at smallest scope.
- **Data is not code — keep channels separate** — boundary validation: never interpolate data into code via strings (SQL/XSS/injection); isolate options from untrusted positional args via `--` delimiter (`cmd -- "$arg"`); keep data in typed data channels (parameterized queries, placeholders, typed args, arrays), never build commands or code by string concatenation; avoid `eval`/string-concat execution.
- **Delimiters lie — use structured over ad-hoc split** — ad-hoc splitting (`split(',')`, newline/token) fails when data contains delimiter; prefer delimiters that cannot appear in data or structured encodings (arrays/JSON/length-prefix); prove delimiter safety if you must split.
- **Platform is a dependency — probe, don't assume** — same API can differ across platforms/versions; declare minimum version, probe capabilities/feature-detect, gate with fallback, fail fast with actionable `install X >=Y`, test on targets.
- **Artifacts: ADR / Blueprint / Technical standards** — ADR is the concise decision log (context → decision → consequences, rejected alternatives); Blueprint is the current model (components, boundaries, interfaces, data/control flow, runtime shape, invariants, risks); Technical standards are reusable rules (naming, layering, dependency direction, FK/deletion policy, API contracts). Update blueprint/standards only when establishing reusable paradigm, not one-off details.
- **Decision framing** — keep reasoning decision-oriented; surface trade-offs explicitly; make rejected alternatives concrete; tie concerns back to boundaries, invariants, and risks.
- **Self-described code** — names reveal intent, functions do one thing, errors fail loud with context, comments explain why not what; `object` forces validation, `Any` silences the checker; reserve `Any` for truly dynamic data or designated transport/IPC zones (file-level suppression only); validate once at admission, trust inside.

## Dispatch

Read the subskill that matches the language you need. Use `Read` (not `Skill` tool — subskills hidden from discovery via `managed-by`).

| Language              | Subskill                                            | When to load                                                                                                                                                                 |
| --------------------- | --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `python-expert`       | `$SKILL_DIR/subskills/python-expert/SKILL.md`       | type safety (Pydantic strict), async, testing, design, observability, resilience, resources, jobs, packaging, production — [python-expert](subskills/python-expert/SKILL.md) |
| `typescript-expert`   | `$SKILL_DIR/subskills/typescript-expert/SKILL.md`   | advanced types, Jest, style, tooling, monorepo — [typescript-expert](subskills/typescript-expert/SKILL.md)                                                                   |
| `rust-expert`         | `$SKILL_DIR/subskills/rust-expert/SKILL.md`         | Cargo, borrow checker, lifetimes, Result, async — [rust-expert](subskills/rust-expert/SKILL.md)                                                                              |
| `go-expert`           | `$SKILL_DIR/subskills/go-expert/SKILL.md`           | modules, interfaces, goroutines, table-driven tests — [go-expert](subskills/go-expert/SKILL.md)                                                                              |
| `lua-expert`          | `$SKILL_DIR/subskills/lua-expert/SKILL.md`          | tables, metatables, game loops, Love2D — [lua-expert](subskills/lua-expert/SKILL.md)                                                                                         |
| `cpp-expert`          | `$SKILL_DIR/subskills/cpp-expert/SKILL.md`          | CMake, RAII, templates, GoogleTest — [cpp-expert](subskills/cpp-expert/SKILL.md)                                                                                             |
| `java-expert`         | `$SKILL_DIR/subskills/java-expert/SKILL.md`         | Spring Boot, JPA, Maven/Gradle, JUnit — [java-expert](subskills/java-expert/SKILL.md)                                                                                        |
| `kotlin-expert`       | `$SKILL_DIR/subskills/kotlin-expert/SKILL.md`       | Coroutines/Flow, Compose, Ktor, Gradle — [kotlin-expert](subskills/kotlin-expert/SKILL.md)                                                                                   |
| `swift-expert`        | `$SKILL_DIR/subskills/swift-expert/SKILL.md`        | SwiftUI, actors, Sendable, strict concurrency — [swift-expert](subskills/swift-expert/SKILL.md)                                                                              |
| `php-expert`          | `$SKILL_DIR/subskills/php-expert/SKILL.md`          | Laravel, Eloquent, Pest, auth/policies — [php-expert](subskills/php-expert/SKILL.md)                                                                                         |
| `perl-expert`         | `$SKILL_DIR/subskills/perl-expert/SKILL.md`         | modern Perl 5.36+, Moo, taint, Test2 — [perl-expert](subskills/perl-expert/SKILL.md)                                                                                         |
| `bash-expert`         | `$SKILL_DIR/subskills/bash-expert/SKILL.md`         | defensive Bash, strict mode, quoting, file/temp safety, args, portability, ShellCheck/Bats — [bash-expert](subskills/bash-expert/SKILL.md)                                   |
| `basedpyright-expert` | `$SKILL_DIR/subskills/basedpyright-expert/SKILL.md` | pyright config, diagnostics, stubs, migration — [basedpyright-expert](subskills/basedpyright-expert/SKILL.md)                                                                |

Omitted argument loads only the spine above. For an unknown language, use the closest subskill or escalate — do not invent a new projection in place.

## When to Use vs Neighbors

- **This router:** language-idiomatic implementation, debugging, testing, review; applies clean-code principles above within each language.
- **`adr`:** ADR lifecycle methodology — `adr` owns the full decision log process; this router now owns the architecture foundations (boundaries, trade-offs, DDD) and the lightweight ADR principle.
- **`sysops-expert` / `safety-guard`:** ops, security, privacy — not code style.
- **`basedpyright` subskill vs `tdd-expert`:** type checker config lives here; test strategy lives in `tdd-expert`.

## Migration

**Status: Complete.** All 12 language experts consolidated under `programming-expert` router. Legacy top-level `skills/*-expert` directories retired — subskills are now canonical.

Adding a new language: create `$SKILL_DIR/subskills/<new>-expert/SKILL.md` with `name: <new>-expert` and `managed-by: programming-expert`, append to `manage`, run `validate-deps.py check && lint && context-check`.

## Verification

Each subskill declares its deterministic gate. Router passes when dispatched subskill's gate passes:

```bash
uv run ruff check . && uv run basedpyright && uv run pytest          # python
npx tsc --noEmit && npm test                                           # typescript
cargo check && cargo test && cargo clippy                              # rust
go vet ./... && go test ./...                                          # go
luacheck . && busted                                                   # lua (when present)
shellcheck --enable=all --external-sources **/*.sh && shfmt -i 2 -ci -bn -sr -kp -d . && bats tests/  # bash
```

See subskill for exact command.

## References

- Sources: `skills/programming-expert/subskills/<language>-expert/` — each subskill is self-contained with its `references/` and `scripts/`
- Authoring: `$SKILL_DIR/../ai-engineering-expert/subskills/skill-authoring/SKILL.md`
