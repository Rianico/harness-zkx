---
name: programming-expert
description: >-
  Polyglot language expertise for Python/TypeScript/Rust/Go/Lua/C++/Java/Kotlin/Swift/PHP/Perl and type checking. Use when implementing, debugging, testing, or reviewing code in any language. TRIGGER: python, typescript, rust, go, lua, cpp, java, kotlin, swift, php, perl, basedpyright
arguments: language
argument-hint: |-
  python-expert -- async, Django, PyTorch, testing patterns
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
  basedpyright-expert -- type checker config, diagnostics, stubs
  omitted -- loads router spine and dispatch table only
metadata:
  manage: [python-expert, typescript-expert, rust-expert, go-expert, lua-expert, cpp-expert, java-expert, kotlin-expert, swift-expert, php-expert, perl-expert, basedpyright-expert]
---

# Programming Expert

Polyglot language router — one description, many projections. The 20% that solves 80%: route by language, then delegate to the focused subskill. Subskills are hidden from discovery (`managed-by`) so context cost drops from ~3250 chars (13 descriptions) to ~280 chars (one router).

## Principles

General engineering rules applied by every subskill — language detail varies, principles don't.

- **Clean commits, clear boundaries** — one commit = one intent, conventional `feat|fix|doc:` prefix, atomic bisectable; separate `code` vs `docs` vs `chore`; modules own their boundaries, cross-module only via public contract, no hidden coupling.
- **SOLID** — SRP one reason to change, OCP open for extension closed for modification, LSP substitutability, ISP narrow interfaces, DIP depend on abstractions; apply at module seams, not per-line.
- **Clean architecture** — dependency rule: inner domain knows nothing of outer delivery; ports & adapters at edges, use cases orchestrate, frameworks are plugins; keep I/O at the boundary, typed admission there.
- **ADR** — record any hard-to-reverse, surprising, or traded-off decision as lightweight ADR (`CONTEXT.md` + `docs/adr/`); keep ADR short: context → decision → consequences; link supersession.
- **Self-described code** — names reveal intent, functions do one thing, errors fail loud with context, comments explain why not what; no `Any`/`object` fallbacks inside typed code, validate once at admission, trust inside.

## Dispatch

Read the subskill that matches the language you need. Use `Read` (not `Skill` tool — subskills hidden from discovery via `managed-by`).

| Language              | Subskill                                              | When to load                                                                                             |
| --------------------- | ----------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `python-expert`       | `$SKILL_DIR/subskills/python-expert/SKILL.md`       | async, Django, PyTorch, generics, pytest — [python-expert](subskills/python-expert/SKILL.md)           |
| `typescript-expert`   | `$SKILL_DIR/subskills/typescript-expert/SKILL.md`   | advanced types, Jest, style, tooling, monorepo — [typescript-expert](subskills/typescript-expert/SKILL.md) |
| `rust-expert`         | `$SKILL_DIR/subskills/rust-expert/SKILL.md`         | Cargo, borrow checker, lifetimes, Result, async — [rust-expert](subskills/rust-expert/SKILL.md)         |
| `go-expert`           | `$SKILL_DIR/subskills/go-expert/SKILL.md`           | modules, interfaces, goroutines, table-driven tests — [go-expert](subskills/go-expert/SKILL.md)         |
| `lua-expert`          | `$SKILL_DIR/subskills/lua-expert/SKILL.md`          | tables, metatables, game loops, Love2D — [lua-expert](subskills/lua-expert/SKILL.md)                   |
| `cpp-expert`          | `$SKILL_DIR/subskills/cpp-expert/SKILL.md`          | CMake, RAII, templates, GoogleTest — [cpp-expert](subskills/cpp-expert/SKILL.md)                        |
| `java-expert`         | `$SKILL_DIR/subskills/java-expert/SKILL.md`         | Spring Boot, JPA, Maven/Gradle, JUnit — [java-expert](subskills/java-expert/SKILL.md)                   |
| `kotlin-expert`       | `$SKILL_DIR/subskills/kotlin-expert/SKILL.md`       | Coroutines/Flow, Compose, Ktor, Gradle — [kotlin-expert](subskills/kotlin-expert/SKILL.md)              |
| `swift-expert`        | `$SKILL_DIR/subskills/swift-expert/SKILL.md`        | SwiftUI, actors, Sendable, strict concurrency — [swift-expert](subskills/swift-expert/SKILL.md)         |
| `php-expert`          | `$SKILL_DIR/subskills/php-expert/SKILL.md`          | Laravel, Eloquent, Pest, auth/policies — [php-expert](subskills/php-expert/SKILL.md)                    |
| `perl-expert`         | `$SKILL_DIR/subskills/perl-expert/SKILL.md`         | modern Perl 5.36+, Moo, taint, Test2 — [perl-expert](subskills/perl-expert/SKILL.md)                    |
| `basedpyright-expert` | `$SKILL_DIR/subskills/basedpyright-expert/SKILL.md` | pyright config, diagnostics, stubs, migration — [basedpyright-expert](subskills/basedpyright-expert/SKILL.md) |

Omitted argument loads only the spine above. For an unknown language, use the closest subskill or escalate — do not invent a new projection in place.

## When to Use vs Neighbors

- **This router:** language-idiomatic implementation, debugging, testing, review; applies clean-code principles above within each language.
- **`architecture-expert` / `adr`:** deep system boundaries, trade-offs, DDD and ADR lifecycle methodology — router only applies the ADR *principle* (record the decision), not the full ADR process.
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
```

See subskill for exact command.

## References

- Sources: `skills/programming-expert/subskills/<language>-expert/` — each subskill is self-contained with its `references/` and `scripts/`
- Authoring: `$SKILL_DIR/../ai-engineering-expert/subskills/skill-authoring/SKILL.md`
