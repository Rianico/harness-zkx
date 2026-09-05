# Gotcha — Never Bypass Blocking Signals

Blocking signals are hard gates. Fix at source, do not route around.

---

## 1) Shell trampoline bypass

**When:** `pi-lens` / `git` / CI says `blocking` / `blocking_provenance_untrusted`.

**Don't:** `G=$(echo git)`, `env`, `bash -c`, sub-shells, wrappers, or any trampoline to force `commit`/`push`/`diff`.

**Do:** Fix code/config → `pi-lens` → `0 blocking` → clean `git commit`. Fork/subagent only to land an already-clean commit.

**Check:** `git commit` without `G=`/`eval`/wrapper when `0 blocking`; no trampoline in transcript.

---

## 2) Headless editor bypass

**When:** Same gate, via `GIT_EDITOR=true`, `EDITOR=true`, `GIT_EDITOR=:`, `true`.

**Don't:** Auto-accept a blocked commit/message or skip the gate.

**Do:** Headless only for non-gate plumbing after green — e.g., `GIT_EDITOR=true git rebase --continue` once `git diff --check` clean and `0 blocking`.

**Check:** No `GIT_EDITOR=true`/`EDITOR=true` in blocking transcript except post-green `rebase --continue`.

---

## 3) GitHub access — prefer `gh` CLI

**When:** model needs to access links related to `github` (`github.com` URLs, issues, PRs, API, repos).

**Don't:** `curl https://github.com/...` / `curl https://api.github.com/...` / `fetch` / `fetch_content` for GitHub hosts.

**Do:** Use `gh` clients — `gh issue view <n> --json title,body --repo <owner/repo>`, `gh pr view`, `gh repo view`, `gh api repos/<owner>/<repo>/issues/<n>` (auth, rate-limit, JSON shape). For Actions progress: `gh run list --workflow <name>`, `gh run view <id>`, `gh run watch <id>` — never poll via `curl` or web fetch. `curl`/`fetch` only as fallback when `gh` unavailable or for non-GitHub hosts.

**Check:** No `curl`/`fetch` to `github.com`/`api.github.com` when `gh` is available; `gh` command appears in transcript for GitHub links and Actions progress.

---

## Common

**Taint:** Bypass may make one command succeed but taints shell provenance `untrusted` — blocks all later `commit`/`push`/`diff` until fresh `pi`/terminal. Re-running `pi-lens` clears diagnostics, not provenance.

**Why:** Breaks EDD evidence loop; hides safety signal.

**Escalation:** If false positive, suppress at smallest seam (`// SAFETY:`, `// ast-grep-ignore:`, `# zizmor: ignore[...]`) with invariant — do not bypass.
