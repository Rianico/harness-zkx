# Gotcha — Never Bypass Blocking Signals

Blocking signals are hard gates. Never bypass verification. Fix failures at the source.

---

## 0) Never skip gates or verification

- **Trigger:** Any gate blocks (`pi-lens`, `wt` pre-merge, CI tests, typecheck, lint).
- **Prohibited:** Never use `--no-verify`, `--no-gpg-sign`, `--force`, or raw `git worktree add` and `git merge`.
- **Prohibited:** Never disable gates or alter tooling configs (`.config/wt.toml`, `.githooks/`, linter configs, CI workflows) to silence errors.
- **Action:** Fix code, config, or tests at source until all gates pass green.
- **False positives:** Suppress only at the narrowest seam with invariant and owner (`// SAFETY:`, `// ast-grep-ignore:`).

---

## 1) Shell trampoline bypass

- **Trigger:** Tooling flags blocking errors or untrusted provenance.
- **Prohibited:** Never use `G=$(echo git)`, `env`, `bash -c`, or wrappers to force execution.
- **Action:** Fix root causes until diagnostics report zero blocking items. Then run clean commands.

---

## 2) Headless editor bypass

- **Trigger:** Commit or rebase blocked by a gate.
- **Prohibited:** Never set `GIT_EDITOR=true` or `EDITOR=:` to auto-accept blocked commits.
- **Action:** Use headless editor only for non-gate plumbing after all checks pass green.

---

## 3) GitHub access — prefer `gh` CLI

- **Trigger:** Accessing GitHub URLs, issues, pull requests, actions, or APIs.
- **Prohibited:** Never scrape GitHub with `curl` or web fetch tools when `gh` is available.
- **Action:** Use `gh` commands (`gh issue`, `gh pr`, `gh run`, `gh api`).
- **Multi-remote:** Always pass `--repo <owner/repo>` on repo-scoped `gh` calls (see `git-convention §2`).

---

## 4) GitHub repo exploration — clone once, read locally

- **Trigger:** Exploring code or history in a GitHub repository.
- **Prohibited:** Never fetch files one by one over HTTP.
- **Action:** Clone shallowly once to a temporary directory: `gh repo clone <owner/repo> $(mktemp -d)/<repo> -- --depth 1`.
- **Action:** Inspect locally using `rg`, `fd`, and local file readers.

---

## Common

- **Taint:** Bypassing gates taints shell provenance as untrusted. This blocks future actions until terminal restart.
- **Evidence:** Bypasses break the EDD evidence loop. Verification requires real tool output.
- **Escalation:** Suppress false positives at the smallest seam with a documented invariant. Never bypass gates.
