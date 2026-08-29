# Gotcha — Never Bypass Blocking Signals

Blocking signals are hard gates, not soft warnings. Treat them as build failures that must be fixed at the source, not routed around.

## Rule

- **Do not bypass blocking diagnostics with shell indirection, wrapper scripts, `G=$(echo git)`, `env`, `bash -c`, sub-shells, or any other trampoline.** If `pi-lens` / `git` / CI says `blocking` / `blocking_provenance_untrusted`, the correct fix is to make the work clean, then run the same command again in a clean way.
- A bypass may make one command succeed, but it **taints the shell's provenance** (`untrusted`) and blocks every later `git commit/push/diff` in that same shell until a fresh session. Re-running `pi-lens` clears diagnostic blockings, not provenance — only a fresh `pi` / fresh terminal clears provenance.
- Prefer: fix the code/config that caused the blocking → `pi-lens` → `0 blocking` → normal `git commit` in a clean shell. Use a fresh fork/subagent only to land an already-clean commit, not to hide a dirty one.

## Why

Bypasses destroy the evidence loop (EDD). They hide the very signal that proves the change is safe to merge and leave the branch in a state that cannot be pushed or reviewed without another bypass.

## Check

- `git commit` without `G=` / `eval` / wrapper succeeds after `pi-lens` reports `0 blocking`.
- No `G=$(echo git)` or equivalent appears in the session transcript for a blocking-gated repo.

## Escalation

If a blocking looks like a false positive, explicitly mark it with the tool's suppression contract (`// SAFETY:`, `// ast-grep-ignore:`, `# zizmor: ignore[...]`) at the smallest seam and document the invariant — do not bypass the gate.
