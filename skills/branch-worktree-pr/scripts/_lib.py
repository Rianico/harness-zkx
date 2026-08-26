#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""Shared typed helpers for branch-worktree-pr Python shims.

Gate ownership: .config/wt.toml [pre-merge].gate is single writer.
Scripts delegate to wt/gh/git via subprocess list args (no shell=True
for user inputs); gate string from wt.toml is trusted.
"""

from __future__ import annotations

import json
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Worktree:
    branch: str
    path: str
    is_current: bool


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    """Run a command with list args, no shell injection."""
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)


def detect_stack_gate(cwd: Path | None = None) -> str | None:
    """Sniff cwd for stack files and return gate string per ADR table.

    Priority: Cargo.toml > pyproject.toml > package.json > deno.json > bun.lockb.
    """
    base: Path = cwd if cwd is not None else Path.cwd()
    if (base / "Cargo.toml").is_file():
        return "cargo test && cargo clippy -- -D warnings"
    if (base / "pyproject.toml").is_file():
        return "uv run ruff check . && uv run basedpyright && uv run pytest -q"
    if (base / "package.json").is_file():
        return "npm run typecheck && npm test"
    if (base / "deno.json").is_file() or (base / "deno.jsonc").is_file():
        return "deno task check && deno test"
    if (base / "bun.lockb").is_file():
        return "bun run typecheck && bun test"
    return None


def scaffold_wt_config(template_path: Path, dest: Path) -> str:
    """Copy template to dest, patch gate line with detected gate.

    Returns the gate string. Raises FileNotFoundError with actionable message
    when stack cannot be detected.
    """
    gate: str | None = detect_stack_gate(Path.cwd())
    if gate is None:
        raise FileNotFoundError(
            "missing .config/wt.toml — run wt config create --project "
            "and merge wt-template.toml; set [pre-merge].gate for your stack"
        )
    if not template_path.is_file():
        raise FileNotFoundError(f"template not found: {template_path}")
    text: str = template_path.read_text(encoding="utf-8")
    # Patch first gate = "..." occurrence (handles single or double quotes)
    patched: str = re.sub(
        r'gate\s*=\s*["\'][^"\']*["\']',
        f'gate = "{gate}"',
        text,
        count=1,
    )
    # If no substitution happened (gate line missing), append under [pre-merge]
    if patched == text and "gate" not in text:
        if "[pre-merge]" in patched:
            patched = patched.replace("[pre-merge]", f'[pre-merge]\ngate = "{gate}"', 1)
        else:
            patched = patched + f'\n[pre-merge]\ngate = "{gate}"\n'
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(patched, encoding="utf-8")
    return gate


def read_gate(cwd: Path | None = None) -> str:
    """Return [pre-merge].gate from .config/wt.toml.

    If file is absent, auto-scaffold from references/wt-template.toml patched
    by stack sniffing (once). If file exists but gate cannot be parsed, raises.
    """
    base: Path = cwd if cwd is not None else Path.cwd()
    dest: Path = base / ".config" / "wt.toml"
    if not dest.is_file():
        # locate template — try sibling references, then skill dir, then cwd skill path
        candidates: list[Path] = [
            Path(__file__).resolve().parent.parent / "references" / "wt-template.toml",
            base / "skills" / "branch-worktree-pr" / "references" / "wt-template.toml",
            Path(__file__).resolve().parent / "wt-template.toml",
        ]
        template: Path | None = next((p for p in candidates if p.is_file()), None)
        if template is None:
            gate_sniff: str | None = detect_stack_gate(base)
            if gate_sniff is None:
                raise FileNotFoundError(
                    "missing .config/wt.toml — run wt config create --project "
                    "and merge wt-template.toml; set [pre-merge].gate for your stack"
                )
            # minimal scaffold when template truly absent
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(f'[pre-merge]\ngate = "{gate_sniff}"\n', encoding="utf-8")
            return gate_sniff
        return scaffold_wt_config(template, dest)

    text: str = dest.read_text(encoding="utf-8")
    gate: str | None = None

    # Try tomllib (stdlib >=3.11) for structured parse
    try:
        import tomllib  # type: ignore[import-not-found]

        with dest.open("rb") as f:
            data: object = tomllib.load(f)
        if isinstance(data, dict):
            pre = data.get("pre-merge")
            if isinstance(pre, dict):
                raw = pre.get("gate")
                if isinstance(raw, str) and raw.strip():
                    gate = raw.strip()
    except Exception:
        gate = None

    if gate is None:
        m: re.Match[str] | None = re.search(r'gate\s*=\s*"([^"]+)"', text)
        if m:
            gate = m.group(1)
        else:
            m2: re.Match[str] | None = re.search(r"gate\s*=\s*'([^']+)'", text)
            if m2:
                gate = m2.group(1)

    if gate is None or not gate.strip():
        raise ValueError(f"could not parse [pre-merge].gate in {dest}")

    return gate.strip()


def wt_list(cwd: Path | None = None) -> list[Worktree]:
    """List worktrees via wt if available, else git worktree list --porcelain."""
    base: Path | None = cwd
    # Try wt first
    try:
        result: subprocess.CompletedProcess[str] = run(["wt", "list", "--format=json"], cwd=base)
        if result.returncode == 0 and result.stdout.strip():
            data: object = json.loads(result.stdout)
            if isinstance(data, list):
                worktrees: list[Worktree] = []
                for entry in data:
                    if not isinstance(entry, dict):
                        continue
                    branch_raw: object = entry.get("branch")
                    path_raw: object = entry.get("path")
                    cur_raw: object = entry.get("is_current")
                    if cur_raw is None:
                        cur_raw = entry.get("isCurrent", False)
                    branch: str = str(branch_raw) if isinstance(branch_raw, str) else ""
                    # wt may return branch as refs/heads/... — normalize
                    if branch.startswith("refs/heads/"):
                        branch = branch[len("refs/heads/") :]
                    path: str = str(path_raw) if isinstance(path_raw, str) else ""
                    is_current: bool = bool(cur_raw) if isinstance(cur_raw, bool) else False
                    # fallback: if wt marks is_current non-bool as string
                    if not isinstance(cur_raw, bool) and isinstance(cur_raw, str):
                        is_current = cur_raw.lower() in ("true", "1", "yes")
                    worktrees.append(Worktree(branch=branch, path=path, is_current=is_current))
                if worktrees:
                    return worktrees
    except FileNotFoundError as _exc:
        print_err(f"wt not found, falling back to git: {_exc}")
    except json.JSONDecodeError as _exc:
        print_err(f"wt list JSON decode failed: {_exc}")
    except Exception as _exc:
        print_err(f"wt list unexpected error: {_exc}")

    # Fallback to git worktree list --porcelain
    result = run(["git", "worktree", "list", "--porcelain"], cwd=base)
    if result.returncode != 0:
        raise RuntimeError(f"git worktree list failed: {result.stderr}")

    blocks: list[dict[str, str]] = []
    block: dict[str, str] = {}
    for raw_line in result.stdout.splitlines():
        line: str = raw_line.strip()
        if not line:
            if block:
                blocks.append(block)
                block = {}
            continue
        if line.startswith("worktree "):
            if block and "worktree" in block:
                blocks.append(block)
                block = {}
            block["worktree"] = line[len("worktree ") :].strip()
        elif line.startswith("branch "):
            block["branch"] = line[len("branch ") :].strip()
        elif line.startswith("HEAD "):
            block["head"] = line[len("HEAD ") :].strip()
    if block:
        blocks.append(block)

    cwd_resolved: Path = (base if base is not None else Path.cwd()).resolve()
    fallback: list[Worktree] = []
    for b in blocks:
        wt_path: str = b.get("worktree", "")
        branch_ref: str = b.get("branch", "")
        branch = ""
        if branch_ref.startswith("refs/heads/"):
            branch = branch_ref[len("refs/heads/") :]
        elif branch_ref:
            branch = branch_ref
        is_current = False
        try:
            is_current = Path(wt_path).resolve() == cwd_resolved
        except Exception:
            is_current = False
        fallback.append(Worktree(branch=branch, path=wt_path, is_current=is_current))
    return fallback


def git_status_clean(
    allow_prefixes: list[str] | None = None,
    cwd: Path | None = None,
) -> tuple[bool, list[str]]:
    """Return (is_clean, bad_lines) filtering allowed untracked prefixes."""
    if allow_prefixes is None:
        allow_prefixes = [".lsz/tmp", "tmp/pi-open-tui"]
    result: subprocess.CompletedProcess[str] = run(["git", "status", "--porcelain"], cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(f"git status failed: {result.stderr}")
    bad: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        raw_path: str = line[3:] if len(line) > 3 else line.strip()
        # handle renames: "R  old -> new"
        if " -> " in raw_path:
            raw_path = raw_path.split(" -> ")[-1].strip()
        raw_path = raw_path.strip().strip('"')
        allowed: bool = False
        for prefix in allow_prefixes:
            norm_prefix: str = prefix.rstrip("/")
            if raw_path == norm_prefix or raw_path.startswith(norm_prefix + "/"):
                allowed = True
                break
        if not allowed:
            bad.append(line)
    return (len(bad) == 0, bad)


def current_branch(cwd: Path | None = None) -> str:
    """Return current branch name or raise."""
    result: subprocess.CompletedProcess[str] = run(["git", "branch", "--show-current"], cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(f"git branch --show-current failed: {result.stderr}")
    branch: str = result.stdout.strip()
    if not branch:
        raise RuntimeError("could not determine current branch (detached HEAD?)")
    return branch


def ensure_clean_worktree(
    allow_prefixes: list[str] | None = None,
    cwd: Path | None = None,
) -> None:
    """Raise if worktree is not clean (excluding allowed prefixes)."""
    is_clean: bool
    bad: list[str]
    is_clean, bad = git_status_clean(allow_prefixes, cwd=cwd)
    if not is_clean:
        raise RuntimeError(f"worktree not clean: {bad}")


def run_gate(gate: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    """Execute trusted gate string from wt.toml without shell.

    The gate is trusted (single writer .config/wt.toml). Split on '&&'
    and run each segment sequentially with shell=False (shlex.split),
    stopping on first failure to preserve '&&' semantics.
    """
    parts: list[str] = [p.strip() for p in gate.split("&&")]
    last: subprocess.CompletedProcess[str] | None = None
    for part in parts:
        if not part:
            continue
        try:
            args: list[str] = shlex.split(part)
        except ValueError as exc:
            return subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr=f"gate parse error: {exc}"
            )
        if not args:
            continue
        last = subprocess.run(args, capture_output=True, text=True, cwd=cwd)
        if last.returncode != 0:
            return last
    if last is None:
        return subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    return last


def has_conflict_markers(file_path: Path) -> bool:
    """Return True if file contains git conflict markers."""
    try:
        text: str = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False
    return "<<<<<<<" in text or "=======" in text or ">>>>>>>" in text


def print_err(msg: str) -> None:
    print(msg, file=sys.stderr)


def ensure_git_repo(cwd: Path | None = None) -> None:
    cmd: list[str] = ["git", "rev-parse", "--is-inside-work-tree"]
    result: subprocess.CompletedProcess[str] = run(cmd, cwd=cwd)
    if result.returncode != 0 or result.stdout.strip() != "true":
        raise RuntimeError("not inside a git repository")


__all__ = [
    "Worktree",
    "current_branch",
    "detect_stack_gate",
    "ensure_clean_worktree",
    "ensure_git_repo",
    "git_status_clean",
    "has_conflict_markers",
    "print_err",
    "read_gate",
    "run",
    "run_gate",
    "scaffold_wt_config",
    "wt_list",
]
