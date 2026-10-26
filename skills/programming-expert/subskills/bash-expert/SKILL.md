---
name: bash-expert
description: >-
  Defensive Bash/POSIX scripting guide with strict mode, safety, and Bats/ShellCheck testing. Use when writing, reviewing, or debugging shell scripts, CI pipelines, and automation.
argument-hint: |-
  [strict|quoting|file-ops|args|portability|safety|testing|tooling|all]
metadata:
  managed-by: programming-expert
meta:
  sources:
    - https://www.skills.sh/pproenca/dot-skills/shell
    - https://www.skills.sh/wshobson/agents/bash-defensive-patterns
    - https://www.skills.sh/sickn33/agentic-awesome-skills/bash-scripting
    - https://www.skills.sh/rmyndharis/antigravity-skills/bash-pro
    - https://www.skills.sh/vudovn/ag-kit/bash-linux
    - https://www.skills.sh/sickn33/agentic-awesome-skills/linux-shell-scripting
    - https://www.skills.sh/wshobson/agents/error-handling-patterns
    - https://www.skills.sh/wshobson/agents/bats-testing-patterns
    - https://github.com/sickn33/agentic-awesome-skills/blob/main/skills/os-scripting/SKILL.md
---

# Bash Expert Skill

Domain knowledge for production Bash — safe, portable, testable, and observable. Synthesizes 9 upstream sources into one spine: strict mode, quoting, defensive patterns, and tooling.

> **Strict mode + quoting is the spine.** Every other section degrades without it. Fail loud, quote always, trap cleanup.

> [!tip] Attribution
> Sources: [sources.md](references/sources.md) — 9 upstream skills, scrape commands, and the audit trail.

## When to Use — Trigger Matrix

| Trigger in your task                                           | Load this section               |
| -------------------------------------------------------------- | ------------------------------- |
| `set -euo pipefail`, `trap`, `ERR`, `pipefail`, exit codes     | §1 Strict Mode & Error Handling |
| `"$var"`, `"$@"`, `$( )`, quoting, globbing, word splitting    | §2 Quoting & Expansion          |
| arrays, `local`, `readonly`, `${var:-}`, parameter expansion   | §3 Variables & Data             |
| `mktemp`, `find -print0`, NUL-safe, temp cleanup, injection    | §4 File & Temp Safety           |
| `getopts`, `--help`, `--dry-run`, input validation             | §5 Argument Parsing             |
| `#!/usr/bin/env bash`, `bashisms`, GNU vs BSD, `checkbashisms` | §6 Portability                  |
| `[[ ]]` vs `[ ]`, `(( ))`, `case`, conditionals                | §7 Conditionals & Tests         |
| performance, builtins vs external, subshells                   | §8 Performance                  |
| `shellcheck`, `shfmt`, `bats`, pre-commit, CI                  | §9 Tooling & Testing            |
| Production script from scratch                                 | §10 Quality Checklist + template |

If task matches two rows, read both sections plus `references/` for overlapping pattern.

## 1. Strict Mode & Error Handling — Most Important

> Read this section on every invocation. Other sections degrade without it.

**Rule: fail loud, never silent.** Every error path has explicit branch — handle, trap, or propagate with context. Never swallow failures.

```bash
#!/usr/bin/env bash
set -Eeuo pipefail          # -E inherit ERR trap, -e exit on error, -u undefined var, pipefail
shopt -s inherit_errexit 2>/dev/null || true  # Bash 4.4+ better propagation
IFS=$'\n\t'                 # prevent word splitting on spaces
```

- `set -E` — ERR trap inherits into functions/subshells.
- `set -o pipefail` — pipeline fails if any command fails, not just last. Essential for `cmd | grep | awk` chains.
- `trap 'cleanup' EXIT` + `trap 'error_handler $LINENO $?' ERR` — always cleanup temp files, report line.
- `trap 'cleanup; exit 130' INT` and `trap 'cleanup; exit 143' TERM` — signal traps must clean up and re-signal or exit with 128+SIG so supervisors/callers detect interruption.
- Send errors to stderr: `printf 'ERROR: %s\n' "$msg" >&2; return 1` or `exit 1` at top-level.
- Use meaningful exit codes: `0` success, `1` general, `2` usage, `64-78` sysexits for CLI.
- Debug opt-in: support `--trace` via `set -x` and `PS4='+ ${BASH_SOURCE}:${LINENO}:${FUNCNAME[0]}: '`.

### Crux: Exit Status Masking in Declarations

`local` and `export` are builtins returning 0. Under `set -e`, combining declaration and command substitution SILENTLY MASKS failures:

```bash
# WRONG — if cmd fails, local returns 0 and script continues!
local output="$(failing_command)"
export token="$(failing_command)"

# CORRECT — declaration separated from assignment
local output
output="$(failing_command)"
export token
token="$(failing_command)"
```

### Crux: Condition Context Errexit Bypass

Inside `if cmd; then`, `while cmd; do`, or `cmd || fallback`, `set -e` is DISABLED for `cmd` AND all functions invoked by `cmd`. Never assume a function will abort on error when called in a condition context:

```bash
# Function called inside if condition runs with set -e DISABLED internally!
if process_payload; then ... fi  # internal errors in process_payload won't abort

# Explicit error checking required:
process_payload || { printf 'process failed\n' >&2; exit 1; }
```

```bash
cleanup() { rm -rf -- "${TMPDIR:-}"; }
trap cleanup EXIT
trap 'cleanup; exit 130' INT
trap 'cleanup; exit 143' TERM
trap 'printf "ERROR at %s:%d (exit %d)\n" "${BASH_SOURCE[0]}" "$LINENO" "$?" >&2' ERR

# Required env var — fail fast with message
: "${REQUIRED_VAR:?REQUIRED_VAR is not set}"

# Timeout external commands
timeout 30s curl --fail --max-time 10 "$url" || { printf 'curl failed\n' >&2; exit 1; }
```

See `$SKILL_DIR/references/defensive-patterns.md` for trap composition, retry with jitter, and idempotency.

## 2. Quoting & Expansion

**Rule: always quote variable expansions.** Unquoted `$var` triggers word splitting + globbing — the #1 Bash bug class.

```bash
# Wrong
cp $source $dest
for f in $(ls *.txt); do echo $f; done
echo $HOME/*.log

# Correct
cp -- "$source" "$dest"
for f in *.txt; do echo "$f"; done                    # glob, not ls
while IFS= read -r -d '' file; do echo "$file"; done < <(find . -print0)

# Argument passing — always "$@"
my_func "$@"

# Command substitution — quote result
content="$(cat "$file")"
files=($(ls))          # wrong — word splitting
mapfile -t files < <(ls)  # correct — null-safe later
```

- Use `"$@"` for forwarding args, `"$*"` only when joining is intentional.
- Prefer `[[ ]]` in Bash (safer, no word splitting), `[ ]` only for POSIX `sh`.
- Use braces for clarity: `"${var}_suffix"` not `"$var_suffix"`.
- Here-docs: `cat <<'EOF'` (quoted) prevents expansion; `cat <<-EOF` strips leading tabs.
- Glob safety: `shopt -s nullglob` / `failglob` / `set -f` to control expansion.

### Crux: Option & Argument Injection Defense

If a variable begins with `-`, commands parse it as a flag instead of a filename/argument:

```bash
# VULNERABLE — if $dir is "-rf /" or $file is "-n", flags trigger!
rm -rf "$dir"
cat "$file"
grep "$pat" "$file"
git checkout "$branch"

# SECURE — terminate options with -- before positional arguments
rm -rf -- "$dir"
cat -- "$file"
grep -F -- "$pat" "$file"
git checkout -- "$branch"
```

### Crux: `printf '%s\n'` over `echo`

`echo "$var"` fails when `$var` equals `-n`, `-e`, `-E`, or starts with `-`. Furthermore, backslash interpretation differs between Bash and POSIX `sh`. Always use `printf '%s\n' "$var"`.

### Crux: NUL Stream Boundaries

Filenames can contain spaces, tabs, and newlines; only `/` and `\0` are invalid in Unix paths. Parsing with `for f in $(cat)` or newline splitting corrupts valid paths. Always use NUL boundaries:

```bash
find . -type f -name '*.txt' -print0 | while IFS= read -r -d '' file; do
  printf 'File: %s\n' "$file"
done
```

## 3. Variables, Arrays & Parameter Expansion

```bash
# Constants — readonly, UPPER_CASE
readonly SCRIPT_NAME="$(basename -- "${BASH_SOURCE[0]}")"
readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# Function locals — always local
my_func() {
  local -r input="$1"
  local output
  output="$(some_command)"  # separated declaration & assignment
  local -a items=()
}

# Associative arrays — Bash 4+
declare -A config=([host]="localhost" [port]="8080")
printf '%s\n' "${config[host]}"

# Safe array iteration
declare -a items=("item 1" "item 2" "*.glob")
for item in "${items[@]}"; do printf 'Processing: %s\n' "$item"; done

# Safe population from command output — NUL or mapfile, never for-in-$( )
mapfile -t lines < <(some_command)
readarray -d '' files < <(find . -print0)

# Parameter expansion — use builtins over external commands
: "${VAR:-default}"          # default value
: "${VAR:?error message}"   # required
echo "${filename%.sh}"       # remove suffix
echo "${path##*/}"           # basename
echo "${text//old/new}"      # replace all
echo "${var@Q}"              # shell-quoted (4.4+), @U upper, @L lower
```

### Crux: Pipeline Subshell State Loss

In standard Unix pipelines, each stage runs in a subshell fork. Variable mutations inside a piped loop do not survive loop exit:

```bash
# BROKEN — RHS executes in a subshell fork; count is lost!
count=0
find . -type f | while IFS= read -r line; do (( count++ )); done
printf 'Total: %d\n' "$count"  # prints 0!

# FIX 1 — Process substitution executes loop in the current shell:
count=0
while IFS= read -r line; do
  (( count++ ))
done < <(find . -type f)
printf 'Total: %d\n' "$count"  # prints actual count

# FIX 2 — shopt -s lastpipe (requires non-interactive shell or set +m)
shopt -s lastpipe
find . -type f | while IFS= read -r line; do (( count++ )); done
```

### Crux: Octal Parsing in Arithmetic

In arithmetic contexts (`$(( ))`, `(( ))`), numbers with leading zeros (e.g. `08`, `09`) are parsed as octal, triggering syntax errors (`value too great for base`). Force decimal parsing:

```bash
# BROKEN on "08" or "09"
month="08"
next_month=$(( month + 1 ))  # syntax error: 08 has invalid octal digit

# FIX — force base 10 or strip leading zeros
next_month=$(( 10#$month + 1 ))
```

- Validate numeric input: `[[ $num =~ ^[0-9]+$ ]] || { printf 'not numeric\n' >&2; exit 1; }`
- Sanitize before use in commands; never `eval "$user_input"` — use arrays for dynamic commands.

## 4. File & Temp Safety

```bash
# Script dir — robust, handles symlinks
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# Temp — mktemp + EXIT trap, never predictable names
TMPDIR="$(mktemp -d)" || { printf 'mktemp failed\n' >&2; exit 1; }
trap 'rm -rf -- "$TMPDIR"' EXIT
TMPFILE="$TMPDIR/work.XXXXXX"
tmpfile="$(mktemp "$TMPDIR/work.XXXXXX")"

# NUL-safe file processing — handles spaces, newlines, globs in filenames
find "$input_dir" -maxdepth 1 -type f -print0 | while IFS= read -r -d '' file; do
  printf 'Processing %s\n' "$file"
done

# Permissions before operations
[[ -r "$file" ]] || { printf 'not readable: %s\n' "$file" >&2; exit 1; }
[[ -w "$dir" ]]  || { printf 'not writable: %s\n' "$dir" >&2; exit 1; }

# Absolute paths for external commands in cron/systemd
command -v rsync &>/dev/null || { printf 'rsync not found\n' >&2; exit 1; }

# Secure file creation — subshell keeps the umask change local
(
  umask 077
  touch "$secure_file"
)
```

- Prefer process substitution `<(command)` over temp files when possible.
- Use `xargs -0` with NUL boundaries for safe orchestration.

## 5. Argument Parsing & Input Validation

```bash
VERBOSE=false; DRY_RUN=false; OUTPUT=""; JOBS=4

usage() {
  cat <<EOF
Usage: $SCRIPT_NAME [OPTIONS] <input>

Options:
  -v, --verbose     Enable verbose output
  -d, --dry-run     Preview without changes
  -o, --output FILE Output file path
  -j, --jobs NUM    Parallel jobs (default: 4)
  -h, --help        Show this help
  --trace           Enable bash trace (set -x)

Examples:
  $SCRIPT_NAME -v -o out.txt input.txt
  $SCRIPT_NAME --dry-run --jobs 8 input.txt
EOF
  exit "${1:-0}"
}

# Long-form + getopts-compatible parsing
while [[ $# -gt 0 ]]; do
  case "$1" in
    -v|--verbose) VERBOSE=true; shift ;;
    -d|--dry-run) DRY_RUN=true; shift ;;
    -o|--output) OUTPUT="$2"; shift 2 ;;
    -j|--jobs) JOBS="$2"; [[ $JOBS =~ ^[0-9]+$ ]] || { printf 'jobs must be numeric\n' >&2; exit 2; }; shift 2 ;;
    -h|--help) usage 0 ;;
    --trace) set -x; shift ;;
    --) shift; break ;;
    -*) printf 'Unknown option: %s\n' "$1" >&2; usage 2 ;;
    *) break ;;
  esac
done
# Remaining positional args in "$@"
```

- Treat input as untrusted. Avoid `eval` and unsafe globbing.
- Support `--dry-run` for destructive operations. Log what would happen.
- Validate with `: "${VAR:?message}"` and `[[ $var =~ ^pattern$ ]]`.

## 6. Portability

| Concern        | Rule                                                                                                      |
| -------------- | --------------------------------------------------------------------------------------------------------- |
| Shebang        | `#!/usr/bin/env bash` for Bash; `#!/bin/sh` only when strict POSIX required                               |
| Bashism check  | `checkbashisms script.sh` + `shellcheck --shell=sh` for POSIX                                             |
| Echo vs printf | Prefer `printf '%s\n' "$var"` — `echo` is non-portable for flags/escapes                                  |
| `sed -i`       | GNU `sed -i` vs BSD `sed -i ''` — detect: `case "$(uname -s)" in Darwin*) sed -i '' ;; *) sed -i ;; esac` |
| `cat -A`       | GNU-only; fails on BSD/macOS (`illegal option -- A`). On macOS use `cat -vet`, `gcat -A`, `od -c`, or `xxd` |
| Exports        | `VAR=value; export VAR` is portable; `export VAR=value` is Bashism in strict POSIX                        |
| Test           | `[[ ]]` Bash-only; `[ ]` + `case` for POSIX; `(( ))` arithmetic is Bash/Ksh                               |

```bash
# Version gate for modern features
if (( BASH_VERSINFO[0] > 5 || (BASH_VERSINFO[0] == 5 && BASH_VERSINFO[1] >= 2) )); then
  : # use Bash 5.2 features: varredir_close, EPOCHREALTIME
fi

# Platform detection
case "$(uname -s)" in
  Linux*)  platform=linux ;;
  Darwin*) platform=macos ;;
  *)       platform=unknown ;;
esac

# Display non-printing characters / line endings portably
case "$(uname -s)" in
  Darwin*) cat_show_all="cat -vet" ;; # BSD cat lacks GNU -A; gcat -A, od -c, xxd also work
  *)       cat_show_all="cat -A" ;;
esac

# Command existence — never which
command -v jq &>/dev/null || { printf 'jq required\n' >&2; exit 1; }
```

- Document the minimum Bash version in the header. Test on Linux, macOS, and BSD.
- Use builtins over external commands when possible for portability.

## 7. Conditionals & Tests

```bash
# Bash — prefer [[ ]] (no word splitting, regex, &&/|| inside)
if [[ -f "$file" && -r "$file" ]]; then content=$(<"$file"); fi
if [[ -z "${VAR:-}" ]]; then printf 'VAR empty\n' >&2; fi
if [[ $num =~ ^[0-9]+$ ]]; then printf 'numeric\n'; fi

# Arithmetic — (( )) not [ ] or test
if (( count > 10 )); then printf 'many\n'; fi
(( count++ )); (( total += n ))

# Pattern matching — case over if/elif chains
case "$action" in
  start) start_service ;;
  stop)  stop_service ;;
  *)     printf 'Unknown: %s\n' "$action" >&2; exit 2 ;;
esac

# POSIX fallback — [ ] with quoted vars
if [ -f "$file" ] && [ -r "$file" ]; then content=$(cat "$file"); fi
```

## 8. Performance

- Avoid subshells in loops: `while read` not `for i in $(cat file)`.
- Use builtins: `[[ ]]` over `test`, `${var//pattern/repl}` over `sed`, `$(( ))` over `expr`.
- Batch operations: one `sed -e 's/a/b/' -e 's/c/d/'` not two `sed` invocations.
- `mapfile`/`readarray` for efficient array population. Use `readarray -d ''` for NUL.
- Associative arrays for lookups vs repeated `grep`.
- `xargs -P "$(nproc)" -n 1` for parallel independent operations.
- Process line-by-line for large files. Avoid loading entire files into memory.

## 9. Tooling & Testing

### Static Analysis & Formatting

```bash
shellcheck --enable=all --external-sources script.sh   # gate
shfmt -i 2 -ci -bn -sr -kp -d script.sh               # format check (-w to write)
checkbashisms script.sh                               # POSIX portability
```

Suppress at the smallest scope, with a reason:

```bash
# shellcheck disable=SC2086  # Reason: word splitting intended for glob expansion
```

Install steps, `.shellcheckrc`, Makefile targets, pre-commit hooks, and the GitHub Actions matrix live in [tooling.md](references/tooling.md).

### Bats Testing (bats-core)

```bash
#!/usr/bin/env bats

setup() {
  export TMPDIR
  TMPDIR="$(mktemp -d)"
  export SCRIPT="$BATS_TEST_DIRNAME/../script.sh"
}

teardown() { rm -rf -- "$TMPDIR"; }

@test "script succeeds with valid input" {
  run -- "$SCRIPT" --output "$TMPDIR/out.txt" "$BATS_TEST_DIRNAME/fixtures/input.txt"
  [ "$status" -eq 0 ]
  [ -f "$TMPDIR/out.txt" ]
}

@test "fails with missing file" {
  run -- "$SCRIPT" "/nonexistent/file.txt"
  [ "$status" -ne 0 ]
  [[ "$output" == *"not found"* ]]
}

@test "prints usage on --help" {
  run -- "$SCRIPT" --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"Usage:"* ]]
}

@test "handles spaces in filename" {
  touch "$TMPDIR/my file.txt"
  run -- "$SCRIPT" "$TMPDIR/my file.txt"
  [ "$status" -eq 0 ]
}
```

Run: `bats tests/` or `bats --tap tests/ | tee results.tap`

## 10. Production Script Template

Start from the base template in [templates.md](references/templates.md): strict mode, logging, traps, usage, argument parsing, validation, and `main`. It covers 80% of production needs. Backup, monitoring, log-analysis, and network variants live in the same file.

## Quality Checklist

Apply exhaustively. Every item is a blocker:

- [ ] `set -Eeuo pipefail` + `inherit_errexit` + `IFS=$'\n\t'` at top
- [ ] All variable expansions quoted (`"$var"`, `"${arr[@]}"`, `"$@"`)
- [ ] `local var; var=$(cmd)` — declaration separated from command substitution assignment to prevent masking exit status under `set -e`
- [ ] `--` option terminator precedes untrusted positional arguments (`rm -rf -- "$dir"`, `cat -- "$file"`)
- [ ] Pipeline subshell avoided when mutating state (use `< <(cmd)` or `shopt -s lastpipe`)
- [ ] Condition context errexit bypass handled explicitly (`cmd || return 1`)
- [ ] Arithmetic uses `10#$val` for base-10 to avoid octal parsing errors on `08`/`09`
- [ ] Signal traps propagate 128+SIG (`exit 130` on INT, `exit 143` on TERM)
- [ ] Atomic locks avoid TOCTOU races (`mkdir "$lockdir"`, `flock`)
- [ ] `trap cleanup EXIT` for temp files; `trap ... ERR` reports line/exit
- [ ] Inputs validated (`: "${VAR:?msg}"`, `[[ $var =~ ^pattern$ ]]`, file checks)
- [ ] Functions use `local` for all vars, `readonly` for constants
- [ ] Argument parsing handles `--`, `--help`, `--dry-run`, `--trace`, unknown opts
- [ ] NUL-safe file handling (`find -print0 | while IFS= read -r -d ''`)
- [ ] `printf` over `echo` for data; errors to `>&2`
- [ ] `command -v` used for command lookup, never `which`
- [ ] Timeouts wrap external commands
- [ ] `shellcheck --enable=all` passes with no unreasoned suppressions
- [ ] `shfmt -i 2 -ci -bn -sr -kp -d` reports no diff
- [ ] Bats tests cover happy + error + edge + spaces-in-path
- [ ] Shebang is `#!/usr/bin/env bash`
- [ ] Version and platform docs live in the header
- [ ] `--help` and `--version` are implemented
- [ ] Exit codes are documented
- [ ] Tested on target platforms (Linux + macOS)
- [ ] POSIX check run when the shebang is `#!/bin/sh`

## References

Deep content behind pointers (one level from SKILL.md):

- [Defensive Patterns & Checklists](references/defensive-patterns.md) — trap composition, retry/jitter, idempotency, security, observability
- [Templates Library](references/templates.md) — backup, monitoring, user-mgmt, log-analysis, network scripts from linux-shell-scripting + os-scripting
- [Tooling & CI](references/tooling.md) — ShellCheck/shfmt/bats/checkbashisms config, pre-commit, GitHub Actions matrix, semgrep/gitleaks
- Sources: [sources.md](references/sources.md) — 9 upstream skills via `docs-scraper`, scrape commands, audit trail.
