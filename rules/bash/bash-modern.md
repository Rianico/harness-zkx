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

# Modern Bash Tooling & Syntax

Modern Bash 5.x environment setup, safe process idioms, and shell script quality gates.

## Tooling (CRITICAL)

- **ShellCheck:** `shellcheck --enable=all --external-sources` in CI — build tools strip nothing; lint is separate gate. Treat `error`/`warning` as blocking, `info`/`style` as advisory. Fix over `disable`.
- **Formatter:** `shfmt -i 2 -ci -bn -sr -kp -d .` to check, `-w .` to write. Keep one formatter; don't stack with `beautysh`.
- **Testing:** `bats-core` (maintained fork) — `bats tests/` in CI; fixtures in `tests/fixtures/`, helpers in `test_helper.bash`. Always run tests with `run -- "$SCRIPT" "$@"` (note `--`).
- **Package/version:** `#!/usr/bin/env bash` shebang; document min `Bash` version in header (`# Requires: Bash >=4.4`); probe `BASH_VERSINFO` before using `mapfile -d`, `wait -n`, `${var@Q}`, `inherit_errexit`.
- **LSP freshness:** ShellCheck diagnostics are file-based; re-run after edits, don't trust stale CI green.

## Project Configuration

### Strict Base `.shellcheckrc`
```
enable=all
external-sources=true
shell=bash
```

### Formatter Config `.shfmt.toml`
```toml
indent = 2
case_indent = true
binary_next_line = true
switch_case_indent = true
space_redirects = true
keep_padding = true
```
Equivalent CLI flags: `shfmt -i 2 -ci -bn -sr -kp`.

## Language Features (Bash 5.x & Modern Idioms)

- **Arrays:** `declare -a` (indexed) / `declare -A` (associative, Bash 4+) — use arrays for lists, not strings; iterate `"${arr[@]}"`, populate via `mapfile -t`/`readarray -d ''`, never `arr=$(cmd)`.
- **Declaration vs Assignment Separation:**
  - Simple literals: `local -r var="$1"` is safe.
  - Command substitution: NEVER combine `local` or `export` with `$(cmd)`. Builtins return 0 and mask failures under `set -e`. Always write:
    ```bash
    local output
    output="$(failing_command)"
    ```
- **Parameter Expansion:**
  - `${var:-default}`, `${var:?msg}` (admission check)
  - `${var%.sh}`, `${var##*/}` (trim suffix/prefix)
  - `${var//old/new}` (replace all)
  - `${var@Q}` (quote for shell evaluation/logging), `${var@U}` (uppercase), `${var@L}` (lowercase), `${var@a}` (attributes)
- **Arithmetic & Base-10:**
  - Use `(( ))` or `$(( ))`.
  - Always force base-10 for untrusted or zero-padded numbers: `$(( 10#$val ))` to prevent `08`/`09` from being parsed as invalid octal.
- **Option Injection Defense:**
  - Always terminate option parsing with `--` before positional arguments:
    `rm -rf -- "$dir"`, `cat -- "$file"`, `grep -F -- "$pat" "$file"`, `git checkout -- "$ref"`.

## Safe Process & Concurrency Idioms

- **`shopt -s inherit_errexit` (Bash 4.4+):**
  - Inherits `set -e` into command substitutions `$(...)`. Without it, failures inside `$(cmd)` are ignored under `set -e`.
- **Pipeline Subshell State Loss & `lastpipe`:**
  - Standard pipes run each stage in a subshell fork: `cmd | while read -r line; do count+=1; done` loses `count`.
  - Preferred fix: Process substitution feeding current shell:
    ```bash
    while IFS= read -r line; do
      (( count++ ))
    done < <(cmd)
    ```
  - Alternative: `shopt -s lastpipe` (requires non-interactive shell or `set +m` to disable job control).
- **Condition Context Errexit Bypass:**
  - Inside `if cmd; then` or `while cmd; do`, `set -e` is DISABLED for `cmd` and any functions called by `cmd`.
  - Explicit error propagation is required: `cmd || return 1`.
- **Atomic Locks (No TOCTOU):**
  - Never test and set: `[ ! -f "$lock" ] && touch "$lock"` is prone to race conditions.
  - Use atomic directory creation: `mkdir "$lockdir" 2>/dev/null || return 1`.
  - Or use `flock`:
    ```bash
    exec {lock_fd}>"$lockfile"
    flock -n "$lock_fd" || die "Already running"
    ```
- **Signal Trap Propagation:**
  - Trap handlers for `INT` and `TERM` must clean up and re-signal or exit with `128 + signal`:
    ```bash
    trap 'cleanup; exit 130' INT
    trap 'cleanup; exit 143' TERM
    ```

## Bats Test Structure

Bats-core test suite template (`tests/test_script.bats`):

```bash
#!/usr/bin/env bats

setup() {
  export TMPDIR
  TMPDIR="$(mktemp -d)"
  export SCRIPT="$BATS_TEST_DIRNAME/../script.sh"
}

teardown() {
  rm -rf -- "$TMPDIR"
}

@test "succeeds on valid input" {
  run -- "$SCRIPT" --output "$TMPDIR/out.txt" "input"
  [ "$status" -eq 0 ]
  [ -f "$TMPDIR/out.txt" ]
}

@test "fails fast on missing input" {
  run -- "$SCRIPT"
  [ "$status" -ne 0 ]
  [[ "$output" =~ "Usage:" ]]
}
```

## Inline Scripts

For standalone scripts, use strict header with inline metadata:

```bash
#!/usr/bin/env bash
set -Eeuo pipefail
# Requires: Bash >=4.4, shellcheck >=0.9, shfmt >=3.8
shopt -s inherit_errexit 2>/dev/null || true
IFS=$'\n\t'
```

Run checks with:
`shellcheck --enable=all --external-sources script.sh && shfmt -i 2 -ci -bn -sr -kp -d script.sh && bats tests/`
