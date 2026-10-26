# Templates Library — Production Shell Scripts

> Copy-paste templates for common automation tasks. All templates build on the base template below: `set -Eeuo pipefail`, quoted vars, trap cleanup.
> Sources: `sickn33/agentic-awesome-skills/linux-shell-scripting` (7 phases) + `sickn33/agentic-awesome-skills/skills/os-scripting` (7 phases).

## Base Production Script Template

Copy-paste starter — covers 80% of production needs:

```bash
#!/usr/bin/env bash
set -Eeuo pipefail
shopt -s inherit_errexit 2>/dev/null || true
IFS=$'\n\t'

readonly SCRIPT_NAME="$(basename -- "${BASH_SOURCE[0]}")"
readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
readonly VERSION="0.1.0"

# --- globals ---
VERBOSE=false
DRY_RUN=false
OUTPUT=""

# --- logging ---
log()  { printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >&2; }
info() { log "INFO: $*"; }
warn() { log "WARN: $*" >&2; }
die()  { log "ERROR: $*"; exit 1; }
debug() { [[ $VERBOSE == true ]] && log "DEBUG: $*"; }

cleanup() { rm -rf -- "${TMPDIR:-}" 2>/dev/null || true; }
trap cleanup EXIT
trap 'die "Error at ${BASH_SOURCE[0]}:${LINENO} (exit $?)"' ERR

# --- usage ---
usage() {
  cat <<EOF
Usage: $SCRIPT_NAME [OPTIONS] <input>

Options:
  -v, --verbose   Verbose output
  -d, --dry-run   Preview without changes
  -o, --output FILE  Output file
  -h, --help      Show help
  --version       Show version
  --trace         Enable bash trace

Examples:
  $SCRIPT_NAME -v -o out.txt input.txt
  $SCRIPT_NAME --dry-run input.txt
EOF
  exit "${1:-0}"
}

# --- validation ---
validate_input() {
  local -r file="$1"
  [[ -f "$file" ]] || die "File not found: $file"
  [[ -r "$file" ]] || die "Not readable: $file"
}

# --- main ---
main() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -v|--verbose) VERBOSE=true; shift ;;
      -d|--dry-run) DRY_RUN=true; shift ;;
      -o|--output) OUTPUT="$2"; shift 2 ;;
      -h|--help) usage 0 ;;
      --version) printf '%s %s\n' "$SCRIPT_NAME" "$VERSION"; exit 0 ;;
      --trace) set -x; shift ;;
      --) shift; break ;;
      -*) die "Unknown option: $1" ;;
      *) break ;;
    esac
  done

  [[ $# -ge 1 ]] || { usage 2; }
  local -r input="$1"
  validate_input "$input"

  info "Starting $SCRIPT_NAME"
  if [[ $DRY_RUN == true ]]; then
    info "[dry-run] Would process $input -> ${OUTPUT:-stdout}"
    return 0
  fi

  # TMPDIR for work
  TMPDIR="$(mktemp -d)" || die "mktemp failed"
  # ... core logic ...
  info "Done"
}

main "$@"
```

## Backup — Directory + Rotation + Remote

```bash
#!/usr/bin/env bash
set -Eeuo pipefail
readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
backup_dir="/var/backups/app"
source_dir="/srv/app"
max_backups=7
mkdir -p -- "$backup_dir"
trap 'rm -f -- "$backup_dir/.tmp"* 2>/dev/null || true' EXIT

ts="$(date +%Y%m%d_%H%M%S)"
tar -czf "$backup_dir/backup_${ts}.tar.gz" -C "$(dirname -- "$source_dir")" "$(basename -- "$source_dir")"
printf 'Backup created: %s\n' "$backup_dir/backup_${ts}.tar.gz"

# Rotation — keep newest N
mapfile -t old < <(ls -1t "$backup_dir"/backup_*.tar.gz 2>/dev/null | tail -n +$((max_backups + 1)) || true)
for f in "${old[@]}"; do [[ -n "$f" ]] && rm -f -- "$f" && printf 'Rotated: %s\n' "$f"; done

# Remote (optional)
# rsync -avz --delete "$backup_dir/backup_${ts}.tar.gz" "user@remote:/backups/"
```

## System Monitoring — CPU/Disk/Memory + Health Check

```bash
#!/usr/bin/env bash
set -Eeuo pipefail
threshold=90
partition="/"
cpu_usage=$(top -bn1 | grep -E 'Cpu\(s\)' | awk '{print $2}' | cut -d. -f1 || echo 0)
disk_usage=$(df -h -- "$partition" | awk 'NR==2{print $5}' | tr -d '%' || echo 0)

if (( cpu_usage > threshold )); then
  printf 'ALERT CPU %d%% > %d%%\n' "$cpu_usage" "$threshold" >&2
  # mail -s "CPU Alert" admin@example.com <<< "CPU $cpu_usage%"
fi
if (( disk_usage > threshold )); then
  printf 'ALERT DISK %d%% > %d%% on %s\n' "$disk_usage" "$threshold" "$partition" >&2
fi

# Health snapshot
{
  printf 'Health %s\n' "$(date -Is)"; echo "== uptime =="; uptime
  echo "== load =="; cat /proc/loadavg 2>/dev/null || sysctl -n vm.loadavg 2>/dev/null || true
  echo "== memory =="; free -h 2>/dev/null || vm_stat 2>/dev/null || true
  echo "== disk =="; df -h
  echo "== top cpu =="; ps aux --sort=-%cpu 2>/dev/null | head -10 || ps aux | head -10
} | tee "health_$(date +%Y%m%d).log"
```

## Log Analysis — Error Extract + Web Log

```bash
#!/usr/bin/env bash
set -Eeuo pipefail
logfile="${1:-/var/log/syslog}"
[[ -f "$logfile" ]] || { printf 'Not found: %s\n' "$logfile" >&2; exit 2; }
out="error_log_$(date +%Y%m%d).txt"
grep -i -E 'error|fail|critical' -- "$logfile" > "$out" || true
printf 'Extracted %d lines -> %s\n' "$(wc -l < "$out")" "$out"

# Web access — top IPs / URLs / status codes (Apache/Nginx common log)
web_log="${2:-/var/log/nginx/access.log}"
if [[ -f "$web_log" ]]; then
  echo "== Top IPs =="; awk '{print $1}' -- "$web_log" | sort | uniq -c | sort -rn | head -10
  echo "== Top URLs =="; awk '{print $7}' -- "$web_log" | sort | uniq -c | sort -rn | head -10
  echo "== Status ==";  awk '{print $9}' -- "$web_log" | sort | uniq -c | sort -rn
fi
```

## Network — Connectivity + Uptime

```bash
#!/usr/bin/env bash
set -Eeuo pipefail
hosts=("8.8.8.8" "1.1.1.1" "google.com")
for host in "${hosts[@]}"; do
  if ping -c1 -W2 -- "$host" &>/dev/null; then printf '[UP] %s\n' "$host"
  else printf '[DOWN] %s\n' "$host" >&2; fi
done

websites=("https://google.com" "https://github.com")
log="uptime_$(date +%Y%m%d).log"
for url in "${websites[@]}"; do
  if curl --silent --head --fail --max-time 10 -- "$url" &>/dev/null; then printf '[UP] %s\n' "$url" | tee -a -- "$log"
  else printf '[DOWN] %s\n' "$url" | tee -a -- "$log" >&2; fi
done
```

## Security — Password Gen + File Encryption

```bash
#!/usr/bin/env bash
set -Eeuo pipefail
length="${1:-16}"
[[ $length =~ ^[0-9]+$ ]] || { printf 'length must be numeric\n' >&2; exit 2; }
openssl rand -base64 48 | tr -dc 'A-Za-z0-9!@#$%^&*' | head -c "$length"; printf '\n'

# Encrypt/decrypt with AES-256-CBC + PBKDF2
# Encrypt: openssl enc -aes-256-cbc -salt -pbkdf2 -in "$file" -out "$file.enc"
# Decrypt: openssl enc -aes-256-cbc -d -pbkdf2 -in "$file.enc" -out "${file%.enc}"
```

## User Management — Creation + Expiry Report

```bash
#!/usr/bin/env bash
set -Eeuo pipefail
username="${1:?Usage: $0 <username>}"
if id -- "$username" &>/dev/null; then printf 'User %s exists\n' "$username"
else sudo useradd -m -s /bin/bash -- "$username" && printf 'Created %s\n' "$username"
     sudo passwd -- "$username"
fi

# Expiry report
out="password_expiry_$(date +%Y%m%d).txt"
{
  printf 'Password Expiry %s\n' "$(date -Is)"; printf '%s\n' "=============================="
  while IFS=: read -r user _ _ _ _ _ shell; do
    [[ "$shell" == */bash ]] || continue
    exp=$(chage -l -- "$user" 2>/dev/null | grep 'Password expires' | cut -d: -f2 || echo "unknown")
    printf 'User: %s  Expires:%s\n' "$user" "$exp"
  done < /etc/passwd
} > "$out"
printf 'Report -> %s\n' "$out"
```

## Automation — Cron + systemd Timer

```bash
# Cron — edit with crontab -e
# 0 2 * * * /usr/local/bin/backup.sh >> /var/log/backup.log 2>&1
# 0 * * * * /usr/local/bin/monitor.sh

# systemd timer — /etc/systemd/system/backup.service + backup.timer
# [Unit] Description=Daily backup
# [Service] Type=oneshot ExecStart=/usr/local/bin/backup.sh
# [Timer] OnCalendar=daily Persistent=true
# [Install] WantedBy=timers.target
# Enable: systemctl enable --now backup.timer && systemctl list-timers
```

## References

- Source: `sickn33/agentic-awesome-skills/linux-shell-scripting/references/detailed-guide.md` — 7 phases
- Source: `sickn33/agentic-awesome-skills/skills/os-scripting` — diagnostics + automation
