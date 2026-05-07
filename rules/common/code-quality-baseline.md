# Code Quality & Security Baseline

## 1. Coding Style & Principles
- **Immutability (CRITICAL):** ALWAYS create new objects, NEVER mutate existing ones (e.g., `update(orig)` not `modify(orig)`).
- **File Organization:** MANY SMALL FILES > FEW LARGE FILES (200-400 lines typical, 800 max). Organize by feature/domain.
- **Error Handling:** Handle errors explicitly. Never silently swallow errors. Fail fast.
- **Input Validation:** ALWAYS validate at system boundaries.
- **Principles:** Readability First, KISS (Keep It Simple), DRY (extract logic if repeated >3 times), YAGNI (don't build until needed).

## 2. Security Guidelines
- **Mandatory Checks before commit:** No hardcoded secrets, inputs validated, SQL/XSS/CSRF prevention, Auth verified, rate limiting, no sensitive data leaked in errors.
- **Secret Management:** ALWAYS use environment variables/secret manager. NEVER hardcode.
- **Security Protocol:** If an issue is found: STOP, use `security-reviewer` agent, fix CRITICAL issues, rotate exposed secrets.

## 3. Performance Assertions
- **MANDATORY:** When making performance claims, benchmark with real tests first—never guess by theory.
- **Process awareness:** Count subprocess spawns. Each fork/exec has overhead that compounds.
- **Measure wall-clock time** with realistic payloads, not synthetic benchmarks.
- **Example lesson:** Bash was assumed faster than Python for hooks, but measured 3x slower (183ms vs 61ms) due to 34 subprocess spawns vs 0.

## 4. Engineering Principles

### Trust But Verify
After fixing issues, restart/refresh and re-verify. Caches can become stale - a fix that appears successful may not persist.
- Server: Restart daemon after type changes
- Build: Clean build after significant refactors
- Tests: Clear test cache if results seem wrong

### API Visibility Matches Usage
Visibility modifiers should reflect actual usage patterns. Private functions/classes used across modules create warnings and confusion.
- If it's used everywhere, make it public
- If it's truly internal, enforce encapsulation

### Scoped Over Global
Fix issues at the most precise scope possible. Targeted fixes preserve overall safety; global suppressions hide real issues.
1. Fix the actual issue (preferred)
2. Suppress at line/block level
3. Suppress at file level
4. Suppress at project level (avoid)
5. Disable rule globally (never)

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

## 5. Pre-Completion Checklist
- [ ] Code is readable and well-named
- [ ] Functions are small (<50 lines), Files focused (<800 lines), no deep nesting (>4 levels)
- [ ] Proper error handling, validation, and no mutation
- [ ] No hardcoded values or secrets
- [ ] Tests pass
- [ ] Performance claims backed by real measurements (not theory)
