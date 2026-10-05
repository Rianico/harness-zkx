#!/usr/bin/env bash
# install-template.sh — install the canonical gh-router PR template into a repository.
# Copies references/pull_request_template.md to $TARGET/.github/pull_request_template.md,
# refusing to overwrite an existing template unless --force. --check compares bytes only.
# Exit codes: 0 ok · 1 drift or refused · 2 usage · 3 missing tool or source template.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC="${GH_ROUTER_TEMPLATE_SRC:-$SCRIPT_DIR/../references/pull_request_template.md}"

usage() {
  cat <<'EOF'
Usage: install-template.sh [--target DIR] [--check] [--force] [--dry-run] [-h|--help]
Installs the canonical PR template at $TARGET/.github/pull_request_template.md.
--check compares bytes and never writes · --force permits overwrite · --dry-run prints the action.
Exit: 0 ok · 1 drift or refused · 2 usage · 3 missing tool or source template.
EOF
}

target="."
check=0
force=0
dry_run=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --target)
      if [[ $# -lt 2 ]]; then
        echo "error: --target requires a value" >&2
        exit 2
      fi
      target="$2"
      shift 2
      ;;
    --check)
      check=1
      shift
      ;;
    --force)
      force=1
      shift
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    *)
      echo "error: unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

# Usage validation precedes all filesystem work: an empty/whitespace target would resolve
# to /.github/ on a privileged machine, and the flag points at an existing repo root.
if [[ ! $target =~ [^[:space:]] ]] || [[ ! -d $target ]]; then
  echo "error: --target requires a non-empty directory" >&2
  exit 2
fi
if [[ "$(cd "$target" && pwd -P)" == "/" ]]; then
  echo "error: --target requires a non-empty directory" >&2
  exit 2
fi

if [[ ! -f "$SRC" || ! -r "$SRC" ]]; then
  echo "error: source template not found or unreadable: $SRC" >&2
  exit 3
fi

dest_dir="$target/.github"
dest="$dest_dir/pull_request_template.md"

if [[ $check -eq 1 ]]; then
  if [[ -e "$dest" && ! -f "$dest" ]]; then
    echo "refused: $dest is not a regular file"
    exit 1
  fi
  if [[ ! -e "$dest" ]]; then
    echo "missing: $dest"
    exit 1
  fi
  if cmp -s "$SRC" "$dest"; then
    echo "clean: $dest matches the canonical template"
    exit 0
  fi
  echo "drift: $dest differs from the canonical template"
  exit 1
fi

if [[ -e "$dest" && ! -f "$dest" ]]; then
  echo "error: $dest exists and is not a regular file" >&2
  exit 1
fi

if [[ -f "$dest" ]] && cmp -s "$SRC" "$dest"; then
  echo "already installed: $dest is identical to the canonical template"
  exit 0
fi

if [[ -f "$dest" && $force -eq 0 ]]; then
  echo "refused: $dest already exists; pass --force to overwrite" >&2
  exit 1
fi

if [[ $dry_run -eq 1 ]]; then
  if [[ -f "$dest" ]]; then
    echo "dry-run: would overwrite $dest"
  else
    echo "dry-run: would install $dest"
  fi
  exit 0
fi

created_dir=0
if [[ ! -d "$dest_dir" ]]; then
  mkdir -p "$dest_dir"
  created_dir=1
fi
tmp="$(mktemp "$dest_dir/.pull_request_template.XXXXXX")"
cleanup() {
  rm -f "$tmp"
  # Never leave an empty .github/ this run created behind a failed write.
  if [[ $created_dir -eq 1 ]]; then
    rmdir "$dest_dir" 2>/dev/null || true
  fi
}
trap cleanup EXIT
chmod 644 "$tmp"
cat "$SRC" >"$tmp"
mv "$tmp" "$dest"
trap - EXIT
echo "installed: $dest"
