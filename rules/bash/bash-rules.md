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

You are operating in a Bash/POSIX shell codebase.

## Core Bash Standards (80% Base)

- **Formatting:** `shfmt -i 2 -ci -bn -sr -kp` — 2-space indent, case indent, binary ops newline, space redirect. Shebang `#!/usr/bin/env bash`. `snake_case` funcs/vars, `UPPER_CASE` `readonly` constants.
- **Strict header:** `set -Eeuo pipefail; shopt -s inherit_errexit 2>/dev/null || true; IFS=$'\n\t'` at the top of every script. `trap 'cleanup' EXIT` is unconditional and signal-safe.
- **Quoting:** always `"$var"`, `"${arr[@]}"`, `"$@"`. Use `[[ ]]` in Bash. Use `[ ]` only for POSIX `sh`. Never leave expansions unquoted.
- **Output:** always `printf '%s\n' "$var"` over `echo`. `echo` misinterprets values starting with `-n`, `-e`, or `-E` as flags. It also handles backslashes inconsistently across shells.
- **Typed boundaries:** validate once at admission (`: "${VAR:?msg}"`, `[[ $var =~ ^[0-9]+$ ]]`, `[[ -f "$file" ]]`). Trust typed data inside. `eval` and `shell=True` are banned. Pass data via arrays, `"$@"`, or `jq --arg` — never string concatenation.

## Critical Cruxes (What Models Get Wrong)

- **Exit status masking:** builtins `local` and `export` return 0! Under `set -e`, `local x=$(failing_cmd)` SILENTLY MASKS the failure. Always separate declaration and assignment: `local x; x=$(failing_cmd)`. Same for `export x; x=$(cmd)`.
- **Option injection defense:** variables starting with `-` are parsed as flags by commands. Always use the `--` terminator before untrusted positional arguments: `rm -rf -- "$dir"`, `cat -- "$file"`, `grep -F -- "$pat" "$file"`, `git checkout -- "$ref"`.
- **Pipeline subshell state loss:** pipelines execute stages in subshell forks. `cmd | while read -r line; do count+=1; done; echo "$count"` outputs 0 — the mutated state is lost. Fix: use process substitution `< <(cmd)` or `shopt -s lastpipe` (with `set +m`).
- **Condition context errexit bypass:** inside `if cmd; then` or `while cmd; do`, `set -e` is DISABLED for `cmd` AND every function called within `cmd`. Propagate errors explicitly (`cmd || return 1`).
- **NUL stream boundaries:** filenames can contain spaces, tabs, and newlines (only `/` and `\0` are illegal in paths). Parsing with `for f in $(cat)` or newline-delimited streams corrupts paths. Always use `find -print0`, `while IFS= read -r -d '' file`, `xargs -0`, `readarray -d ''`.
- **Octal arithmetic trap:** in arithmetic contexts (`$(( ))`, `(( ))`), leading zeros (e.g. `08`, `09`) parse as octal and trigger syntax errors. Force base-10: `$(( 10#$val ))` or `${val#0}`.
- **Atomic locks vs TOCTOU:** `[ ! -f "$lock" ] && touch "$lock"` is race-prone. Use atomic directory creation `mkdir "$lockdir"`, `(set -C; : > "$lockfile")`, or `flock`.
- **Signal trap propagation:** `SIGINT`/`SIGTERM` traps clean up, then re-signal or exit with `128+SIG` (`exit 130` for INT, `exit 143` for TERM). Callers and supervisors detect the interruption through that exit code.

## Safety & Portability

- **Fix over suppress:** narrowest `shellcheck disable=SCxxxx` with `# Reason:` at line scope. Blanket disables are banned.
- **Fresh diagnostics:** ShellCheck output is file-based. Re-run after edits. Treat stale CI green as unproven.
- **Platform probe:** use `command -v`, never `which`. Declare the minimum Bash version behind a `BASH_VERSINFO` gate. Detect GNU vs BSD with `case "$(uname -s)"` (`sed -i` vs `sed -i ''`, `cat -vet` vs `cat -A`). Run `checkbashisms` for POSIX targets. Fail fast with `install X >=Y`.

## Expertise Routing (Use `Read` tool)

`bash-expert` is a managed subskill of the `programming-expert` router. Subskills are hidden from discovery (`managed-by`) — do not invoke them through the `Skill` tool. Read the file directly:

- `skills/programming-expert/subskills/bash-expert/SKILL.md` — strict mode, quoting, crux blocks, argument parsing, portability, tooling, quality checklist
- `skills/programming-expert/subskills/bash-expert/references/` — defensive patterns, templates (incl. the production script base), tooling & CI config bodies, sources

**CRITICAL:** Do not guess `set -e`/`pipefail`/`trap`/quoting fixes. Read the expert methodology first — permissive defaults hide bugs.
