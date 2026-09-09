---
paths:
  - '**/*.sh'
  - '**/*.bash'
  - '**/*.bats'
  - '**/Makefile'
  - '**/*.mk'
  - '.shellcheckrc'
  - '.shfmt.toml'
---

# Bash Rules

You are operating in a Bash/POSIX shell codebase. Before proceeding, review and apply these rules.

## Core Bash Standards (80% Base)

- **Formatting:** `shfmt -i 2 -ci -bn -sr -kp` — 2-space indent, case indent, binary ops newline, space redirect; `#!/usr/bin/env bash` shebang; `snake_case` funcs/vars, `UPPER_CASE` `readonly` constants.
- **Strict Header:** `set -Eeuo pipefail; shopt -s inherit_errexit 2>/dev/null || true; IFS=$'\n\t'` at top of every script; `trap 'cleanup' EXIT` unconditional, signal-safe.
- **Quoting:** Always `"$var"`, `"${arr[@]}"`, `"$@"`; `[[ ]]` in Bash, `[ ]` only for POSIX `sh`; never leave expansions unquoted.
- **Output:** Always `printf '%s\n' "$var"` over `echo` — `echo` misinterprets values starting with `-n`, `-e`, `-E` as flags and handles backslashes inconsistently across shells.
- **Typed Boundaries:** Validate once at admission (`: "${VAR:?msg}"`, `[[ $var =~ ^[0-9]+$ ]]`, `[[ -f "$file" ]]`), trust typed inside; no `eval`/`shell=True`; data via arrays/`"$@"`/`jq --arg`, never string concatenation.

## Critical Cruxes (What Models Get Wrong)

- **Exit status masking:** Builtins `local` and `export` return 0! Under `set -e`, `local x=$(failing_cmd)` SILENTLY MASKS the failure. Always separate declaration and assignment: `local x; x=$(failing_cmd)`. Same for `export x; x=$(cmd)`.
- **Option injection defense:** Variables starting with `-` are parsed as flags by commands. Always use `--` terminator before untrusted positional arguments: `rm -rf -- "$dir"`, `cat -- "$file"`, `grep -F -- "$pat" "$file"`, `git checkout -- "$ref"`.
- **Pipeline subshell state loss:** Pipelines execute stages in subshell forks: `cmd | while read -r line; do count+=1; done; echo "$count"` outputs 0! Mutated state is lost. Fix: use process substitution `< <(cmd)` or `shopt -s lastpipe` (with `set +m`).
- **Condition context errexit bypass:** Inside `if cmd; then` or `while cmd; do`, `set -e` is DISABLED for `cmd` AND every function called within `cmd`. Never rely on `set -e` inside conditional tests; use explicit error propagation (`cmd || return 1`).
- **NUL stream boundaries:** Filenames can contain spaces, tabs, and newlines (only illegal characters are `/` and `\0`). Parsing with `for f in $(cat)` or newline-delimited streams is broken. Always use `find -print0`, `while IFS= read -r -d '' file`, `xargs -0`, `readarray -d ''`.
- **Octal arithmetic trap:** In arithmetic contexts (`$(( ))`, `(( ))`), numbers with leading zeros (e.g. `08`, `09`) are interpreted as octal and trigger syntax errors. Force base-10: `$(( 10#$val ))` or `${val#0}`.
- **Atomic locks vs TOCTOU:** `[ ! -f "$lock" ] && touch "$lock"` is vulnerable to race conditions. Use atomic directory creation `mkdir "$lockdir"`, `(set -C; : > "$lockfile")`, or `flock`.
- **Signal trap propagation:** Trapping `SIGINT`/`SIGTERM` must clean up and re-signal or exit with 128+SIG (`exit 130` for INT, `exit 143` for TERM) so callers/supervisors detect the termination signal properly.

## Safety & Portability

- **Fix over suppress:** Narrowest `shellcheck disable=SCxxxx` with `# Reason:` at line scope; never blanket-disable.
- **Platform probe:** `command -v` not `which`; declare min `Bash` version (`BASH_VERSINFO` gate), `case "$(uname -s)"` for GNU vs BSD (`sed -i` vs `sed -i ''`), `checkbashisms` for POSIX; fail fast with `install X >=Y`.

## Expertise Routing (Use `Skill` tool)

If your task needs deep methodology, you MUST pause and invoke `Skill` for `programming-expert` (`bash-expert`):

- **Strict/quoting/safety:** `Skill(skill="programming-expert", args="bash-expert strict")` — strict mode, quoting, trap/cleanup, injection, NUL-safe.
- **Args/portability/perf:** `Skill(skill="programming-expert", args="bash-expert portability")` — arg parsing, `getopts`, Bash 5.x, GNU/BSD, builtins.
- **Tooling/testing:** `Skill(skill="programming-expert", args="bash-expert tooling")` — ShellCheck/shfmt/bats, pre-commit, CI matrix, templates.

**CRITICAL:** Do not guess `set -e`/`pipefail`/`trap`/`quoting` fixes without retrieving the expert skill first — permissive defaults hide bugs.
