# Defensive Patterns — Deep Reference

> Companion to `$SKILL_DIR/SKILL.md` §1, §4, §5. Covers trap composition, retry, idempotency, security, and observability. Based on `pproenca/dot-skills/shell` 49 rules + `bash-pro` production patterns.

## Trap Composition

Traps stack — last `trap` for a signal replaces previous. Use helper to compose:

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

cleanup_tmp() { rm -rf -- "${TMPDIR:-}" 2>/dev/null || true; }
cleanup_log() { [[ -n "${LOGFILE:-}" ]] && printf 'exit %d at %s\n' "$?" "$(date -Is)" >> "$LOGFILE"; }

# Compose: run both on EXIT
trap 'cleanup_tmp; cleanup_log' EXIT
trap 'printf "ERROR %s:%d exit %d\n" "${BASH_SOURCE[0]}" "$LINENO" "$?" >&2' ERR
trap 'cleanup_tmp; printf "Interrupted\n" >&2; exit 130' INT
trap 'cleanup_tmp; printf "Terminated\n" >&2; exit 143' TERM
```

- `trap ... ERR` fires on any failed command under `set -e`; use `|| true` to allow expected failures.
- `trap ... EXIT` always fires — idempotent cleanup is required.
- Signal traps (`INT`, `TERM`) must exit with `128 + signal` (`130` for `SIGINT`, `143` for `SIGTERM`) so callers/supervisors recognize signal termination.
- For long-running scripts, trap `SIGHUP SIGINT SIGTERM` for graceful shutdown; kill background jobs: `trap 'kill 0' EXIT` when using `set -m`.

## Retry with Jitter (Transient Only)

Retry only transient failures (`curl 429/502/503/504`, `ConnectionError`, `TimeoutError`). Never retry auth 4xx or `ValueError`.

```bash
# Retry with exponential backoff + jitter
retry() {
  local -r max_attempts="${1:-3}"
  local -r base_delay="${2:-1}"
  shift 2 || true
  local attempt=1 delay
  while true; do
    if "$@"; then return 0; fi
    (( attempt >= max_attempts )) && return 1
    delay=$(awk -v b="$base_delay" -v a="$attempt" 'BEGIN{srand(); printf "%.2f", b*(2^(a-1))*(0.5+rand()*0.5)}')
    printf 'attempt %d/%d failed, retry in %.1fs: %s\n' "$attempt" "$max_attempts" "$delay" "$*" >&2
    sleep "$delay"
    (( attempt++ ))
  done
}

# Usage
retry 5 1 curl --fail --max-time 10 "$url" || die "curl failed after retries"
```

Cap both attempts and wall time; jitter avoids thundering herd.

## Idempotency & Atomic Locking

Design scripts safe to re-run and safe under concurrent execution:

- Check before create: `[[ -f "$file" ]] || create_file`
- Use `mkdir -p`, `ln -sf`, `install -m 644` — not bare `mkdir`/`ln`.
- For package installs: `command -v jq &>/dev/null || install_jq`
- **Atomic Locks (Avoid TOCTOU):** Bare `[ ! -f "$lock" ] && touch "$lock"` has a time-of-check-to-time-of-use race. Use atomic operations:
  ```bash
  # Atomic lock directory
  mkdir "$lockdir" 2>/dev/null || { printf 'Lock held\n' >&2; exit 1; }
  
  # Or file descriptor flock
  exec 200>"$lockfile"
  flock -n 200 || { printf 'Lock held\n' >&2; exit 1; }
  ```

## Security & Robustness

```bash
# Never eval user input — use arrays for dynamic commands
# Wrong: eval "cmd $user_input"
# Correct:
args=()
[[ $verbose == true ]] && args+=(--verbose)
cmd "${args[@]}" -- "$user_input"

# Prevent argument injection — always -- before untrusted data
rm -rf -- "$user_dir"
git checkout -- "$branch"
grep -F -- "$pattern" "$file"

# Exit status masking defense — local/export returns 0!
# Never combine declaration with command substitution:
local payload
payload="$(generate_payload)"

# Errexit bypass in condition contexts
# Inside `if cmd; then` or `while cmd; do`, set -e is disabled within cmd!
check_health || return 1  # explicit bubble, never assume if check_health aborts

# SUID/SGID — never use on shell scripts (safety-suid-forbidden)
# Check file permissions before sensitive ops
[[ -O "$file" ]] || die "Not owner: $file"

# Secrets — from env, never code/logs/errors
: "${API_TOKEN:?API_TOKEN required}"
# Mask in logs: printf '%s' "$token" | sed 's/./*/g'

# Input sanitization — allowlist
[[ $username =~ ^[a-z_][a-z0-9_-]*$ ]] || die "Invalid username"

# Restrictive umask for secrets
(umask 077; printf '%s' "$secret" > "$secure_file")
```

## Observability & Logging

```bash
# Structured logging with levels
LOG_LEVEL=${LOG_LEVEL:-INFO}  # DEBUG, INFO, WARN, ERROR

log_level_num() { case "$1" in DEBUG) echo 0;; INFO) echo 1;; WARN) echo 2;; ERROR) echo 3;; *) echo 1;; esac; }

log() {
  local level="$1"; shift
  (( $(log_level_num "$level") >= $(log_level_num "$LOG_LEVEL") )) || return 0
  printf '[%s] [%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$level" "$*" >&2
  # Optional syslog
  # logger -t "$SCRIPT_NAME" -p "user.${level,,}" "$*"
}

info()  { log INFO "$@"; }
warn()  { log WARN "$@"; }
error() { log ERROR "$@"; }

# JSON structured log for aggregation
json_log() {
  local level="$1" msg="$2"
  printf '{"ts":"%s","level":"%s","msg":%s,"script":"%s"}\n' \
    "$(date -u +%FT%TZ)" "$level" "$(printf '%s' "$msg" | jq -Rs .)" "$SCRIPT_NAME" >&2
}

# Syslog integration
# logger -t "$SCRIPT_NAME" "started with args: $*"

# Metrics export (Prometheus)
# printf 'script_runs_total{script="%s"} 1\n' "$SCRIPT_NAME" >> /var/lib/prometheus/script.prom
```

## Process Orchestration

```bash
# xargs -0 with NUL for safe parallelism
find . -name '*.log' -print0 | xargs -0 -P "$(nproc)" -n 1 gzip

# readarray for safe population
readarray -d '' files < <(find . -type f -print0)
printf 'Found %d files\n' "${#files[@]}"

# wait -n for any job (Bash 5+ / 4.3+)
for host in "${hosts[@]}"; do ping -c1 "$host" & done
wait -n  # wait for first job
```

## References

- Source: `pproenca/dot-skills/shell` — 9 categories, 49 rules; `safety-*`, `err-*`, `perf-*`
- Source: `rmyndharis/antigravity-skills/bash-pro` — § Safety & Security, Observability, Performance
- Source: `wshobson/agents/error-handling-patterns` — resilience patterns
