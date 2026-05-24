# Development Patterns

## Code Quality

### Immutability (CRITICAL)
ALWAYS create new objects, NEVER mutate existing ones (e.g., `update(orig)` not `modify(orig)`).

### File Organization
MANY SMALL FILES > FEW LARGE FILES (200-400 lines typical, 800 max). Organize by feature/domain.

### Error Handling
Handle errors explicitly. Never silently swallow errors. Fail fast.

### Principles
Readability First, KISS (Keep It Simple), DRY (extract logic if repeated >3 times), YAGNI (don't build until needed).

### API Visibility Matches Usage
Visibility modifiers should reflect actual usage patterns. Private functions/classes used across modules create warnings and confusion.
- If it's used everywhere, make it public
- If it's truly internal, enforce encapsulation

### Scoped Over Global
Fix issues at the most precise scope possible. Targeted fixes preserve overall safety; global suppressions hide real issues.

**Scope Hierarchy (most precise to least):**
1. **Fix the code** (preferred) — Address the actual issue
2. **Line-level suppression** — Single instance, document why
3. **File-level suppression** — Pattern in one file, document why
4. **Targeted config** — Category-level (e.g., `allowedUntypedLibraries` for internal packages)
5. **Project-level disable** — Last resort, signals potential architectural issue
6. **Disable rule globally** — Never

**Category-Level Thinking:**
When a diagnostic appears 50+ times for the same category (e.g., internal modules without stubs), use targeted config instead of 50+ line suppressions. This signals intent clearly and reduces noise.

**Document Every Suppression:**
```python
# <tool>: ignore[<rule>]
# Reason: <one-line explanation of why this suppression is legitimate>
```

### Respect LSP Diagnostics (CRITICAL)

LSP diagnostics (basedpyright, tsc, rust-analyzer, gopls, etc.) are authoritative signals. Treat all diagnostics as blockers until triaged — fix or suppress, never ignore. See ai-engineering-expert "Respect Tool Feedback" for full methodology.

---

## Types & Data Flow

### Input Validation
ALWAYS validate at system boundaries.

### Validate at Boundaries
Dynamic data enters at boundaries; validate there, not everywhere. Once validated, internal code can trust types.
- At API boundaries: validate once with Pydantic/schemas
- Internal code: trust the type, avoid defensive checks everywhere

### Prefer Type-Safe Libraries
Dynamic languages benefit from libraries that enforce type discipline. Prefer matured libs that reduce runtime uncertainty.
- TypeScript over JavaScript for frontend code
- Pydantic over `Any`/`object` for Python data models
- Zod for runtime validation in JS/TS
- serde with derived traits for Rust serialization
- The goal: shift type errors from runtime to compile/validation time

### Keep Typed Models, Serialize at Boundaries
When using validation libraries (Pydantic, Zod, serde), keep typed models as long as possible. Only serialize (`model_dump()`, `toJSON()`) at actual output boundaries.
- WRONG: `config_data = config_obj.model_dump(); languages = config_data.get("languages")` — loses type
- RIGHT: `for lang_name, lang_conf in config_obj.languages.items():` — stays typed

### Serialization/Deserialization at System Boundaries
Serialize only at output boundaries (transport, IPC, API responses). Deserialize only at input boundaries. Application logic works with typed models throughout.
- **Output boundary:** Transport layers, IPC handlers, network clients, file writers
- **Input boundary:** API endpoints, message handlers, file parsers, config loaders
- **Never in application layer:** If you see `model_dump()` or `toJSON()` in business logic, question whether it belongs there
- **Layering check:** When type narrowing seems complex, ask: "Why does this serialization function exist here? Should it move to the boundary?"

---

## Git Workflow

### Test After Conflict Resolution
After resolving git merge/rebase conflicts, run the full test suite before continuing. Conflict resolution is a manual edit that can introduce subtle breakage.
- **Why:** Manual conflict resolution bypasses CI checks and can silently break functionality
- **When:** After `git rebase --continue` or before `git merge --continue`, run tests locally
- **Minimum:** Run tests for files touched by the conflict; ideally run full suite

---

## Language Management

### Single-Language Projects
Use the language's native tool for version and dependency management.
- **Python:** uv (respects `.python-version` or system Python)
- **Rust:** cargo with `rust-toolchain.toml`
- **Node.js:** Use corepack or nvm with `.nvmrc`
- **Why:** Native tools provide better integration, faster operations, and idiomatic workflows

### Multi-Language Projects
Use asdf with `.tool-versions` when a project requires multiple language runtimes.
- **When:** Two or more languages in active development (e.g., Python backend + Node frontend)
- **File:** Commit `.tool-versions` to version control
- **Setup:** `asdf install` after cloning to sync all versions
- **Note:** uv and other tools respect `.tool-versions` when present

### Python Version
Default to Python 3.14 for new projects.
- Single-lang: specify in `.python-version` (uv reads this)
- Multi-lang: specify in `.tool-versions`: `python 3.14.x`

---

## Verification

### Trust But Verify
After fixing issues, restart/refresh and re-verify. Caches can become stale - a fix that appears successful may not persist.
- Server: Restart daemon after type changes
- Build: Clean build after significant refactors
- Tests: Clear test cache if results seem wrong

---

## Security

### Mandatory Checks Before Commit
No hardcoded secrets, inputs validated, SQL/XSS/CSRF prevention, Auth verified, rate limiting, no sensitive data leaked in errors.

### Secret Management
ALWAYS use environment variables/secret manager. NEVER hardcode.

### Security Protocol
If an issue is found: STOP, use `security-reviewer` agent, fix CRITICAL issues, rotate exposed secrets.

---

## Performance

### Benchmark Before Claiming
When making performance claims, benchmark with real tests first—never guess by theory.

### Process Awareness
Count subprocess spawns. Each fork/exec has overhead that compounds.

### Measure Realistically
Measure wall-clock time with realistic payloads, not synthetic benchmarks.
- **Example:** Bash was assumed faster than Python for hooks, but measured 3x slower (183ms vs 61ms) due to 34 subprocess spawns vs 0.

---

## Pre-Completion Checklist
- [ ] Code is readable and well-named
- [ ] Functions are small (<50 lines), Files focused (<800 lines), no deep nesting (>4 levels)
- [ ] Proper error handling, validation, and no mutation
- [ ] No hardcoded values or secrets
- [ ] Tests pass
- [ ] Performance claims backed by real measurements (not theory)
