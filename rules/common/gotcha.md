# Gotcha — Never Bypass Blocking Signals

Blocking signals are hard gates. Never skip, escape, or bypass any gate or verification — fix at source, do not route around.

---

## 0) Never skip / escape / bypass any gate or verification

**When:** any gate blocks — `pi-lens` blocking / `blocking_provenance_untrusted`, `wt` pre-merge / pre-push (`commitlint`, CHANGELOG guard), CI (`tests`, `typecheck`, `lint`).

**Don't:** `--no-verify`, `--no-gpg-sign` bypass, raw `git worktree add` / `git merge` to dodge `wt` hooks, commenting out / disabling any gate, `--force` / force-merge to override, or blanket suppression.

**Do:** fix code/config/docs at source → re-run that gate → green / `0 blocking` → clean operation. If false positive, suppress at smallest seam with invariant + owner (`// SAFETY:`, `// ast-grep-ignore:`, `# zizmor: ignore[...]`) — never bypass.

**Check:** transcript shows no `--no-verify` / raw bypass / disabled gate when blocked; only narrow suppression with reason and invariant.

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

## 4) GitHub repo exploration — clone once, read locally

**When:** model needs to explore a GitHub repo (browse code, compare versions, gather API facts).

**Don't:** `fetch`/`fetch_content` the same repo file-by-file — burns context, rate limits, and repeats on every question.

**Do:** `gh repo clone <owner/repo> $(mktemp -d)/<repo> -- --depth 1` (add `--branch <b>` when version matters), then `rg`/`fd`/`read` locally. Re-clone or `git fetch --depth 1` only when stale.

**Check:** repeated reads against one repo hit local files, not fresh `fetch_content` calls; no more than one clone per repo per session unless ref changes.

---

## Common

**Taint:** Bypass may make one command succeed but taints shell provenance `untrusted` — blocks all later `commit`/`push`/`diff` until fresh `pi`/terminal. Re-running `pi-lens` clears diagnostics, not provenance.

**Why:** Breaks EDD evidence loop; hides safety signal. Skipping any gate defeats verification — the gate is the point.

**Escalation:** If false positive, suppress at smallest seam (`// SAFETY:`, `// ast-grep-ignore:`, `# zizmor: ignore[...]`) with invariant — do not bypass any gate.
