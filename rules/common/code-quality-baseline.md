# Code Quality, Security & Testing Baseline

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

## 3. Testing Requirements
- **Coverage:** Minimum 80% coverage required across Unit, Integration, and E2E tests.
- **Test-Driven Development:** MANDATORY workflow (RED -> GREEN -> IMPROVE).
- **Bug Fixes:** Reproduce the issue with a failing test first when practical.
- **Refactors:** Verify behavior before and after the change.
- **Verification:** Define a concrete verification step for each meaningful implementation step.
- **Troubleshooting:** Check test isolation and mocks before blaming tests. Fix the implementation unless the tests are explicitly wrong.

## 4. Pre-Completion Checklist
- [ ] Code is readable and well-named
- [ ] Functions are small (<50 lines), Files focused (<800 lines), no deep nesting (>4 levels)
- [ ] Proper error handling, validation, and no mutation
- [ ] No hardcoded values or secrets
- [ ] Tests pass with 80%+ coverage
