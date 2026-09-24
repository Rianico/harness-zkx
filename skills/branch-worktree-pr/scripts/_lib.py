#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///

"""Shared typed helpers for branch-worktree-pr Python shims.

Gate ownership: .config/wt.toml [pre-merge].gate is single writer.
Scripts delegate to wt/gh/git via subprocess list args (no shell=True
for user inputs); gate string from wt.toml is trusted.
"""

from __future__ import annotations

import fnmatch
import json
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Worktree:
    branch: str
    path: str
    is_current: bool


# Machine-generated cache artifacts that never carry user intent. `git status --porcelain`
# reports them as untracked the moment a stray interpreter runs without
# PYTHONDONTWRITEBYTECODE=1, which halted convergence admission before round 1 and killed a
# whole batch. Admission tolerates them rather than failing the worktree.
EPHEMERAL_STATUS_PATTERNS: tuple[str, ...] = (
    "*.pyc",
    "*.pyo",
    "__pycache__",
    "*/__pycache__",
    ".DS_Store",
    "*/.DS_Store",
)

# Frozen-lockfile install command per stack, in probe order. The first lockfile found wins.
INSTALL_COMMANDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("pnpm-lock.yaml", ("pnpm", "install", "--frozen-lockfile")),
    ("package-lock.json", ("npm", "ci")),
    ("yarn.lock", ("yarn", "install", "--frozen-lockfile")),
    ("bun.lockb", ("bun", "install", "--frozen-lockfile")),
    ("bun.lock", ("bun", "install", "--frozen-lockfile")),
    ("uv.lock", ("uv", "sync", "--frozen")),
    ("Cargo.lock", ("cargo", "fetch", "--locked")),
)


def run(
    cmd: list[str],
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a command with list args, no shell injection. `env` replaces the inherited env when given."""
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, env=env)


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


def _worktree_from_wt_entry(entry: dict[str, object]) -> Worktree | None:
    """Parse one `wt list --format=json` row, accepting schema 1 and schema 2 shapes.

    Schema 1 (bare array; the wt <= 0.76 default) carries `branch` / `path` / `is_current` on
    the row. Schema 2 (the `[list] json-schema = 2` envelope) nests them: `branch` stays, the
    path moves under `worktree.path`, and `is_current` becomes `worktree.current`. Reading both
    here keeps `wt_list` correct while the format migrates, whichever value the project pins.
    Rows with no path (branch-only rows) are not worktrees and are skipped.
    """
    branch_raw: object = entry.get("branch")
    path_raw: object = entry.get("path")
    cur_raw: object = entry.get("is_current")
    if cur_raw is None:
        cur_raw = entry.get("isCurrent")
    nested: object = entry.get("worktree")
    if isinstance(nested, dict):
        if not isinstance(path_raw, str) or not path_raw:
            path_raw = nested.get("path")
        if cur_raw is None:
            cur_raw = nested.get("current")
    branch: str = branch_raw if isinstance(branch_raw, str) else ""
    # wt may return branch as refs/heads/... — normalize
    if branch.startswith("refs/heads/"):
        branch = branch[len("refs/heads/") :]
    path: str = path_raw if isinstance(path_raw, str) else ""
    if not path:
        return None
    is_current: bool = cur_raw if isinstance(cur_raw, bool) else False
    if isinstance(cur_raw, str):
        is_current = cur_raw.lower() in ("true", "1", "yes")
    return Worktree(branch=branch, path=path, is_current=is_current)


def wt_list(cwd: Path | None = None) -> list[Worktree]:
    """List worktrees via wt if available, else git worktree list --porcelain."""
    base: Path | None = cwd
    # Try wt first
    try:
        result: subprocess.CompletedProcess[str] = run(["wt", "list", "--format=json"], cwd=base)
        if result.returncode == 0 and result.stdout.strip():
            data: object = json.loads(result.stdout)
            entries: object = None
            if isinstance(data, list):
                entries = data  # schema 1: bare array (wt <= 0.76 default)
            elif isinstance(data, dict):
                entries = data.get("items")  # schema 2: { schema, repo, collected, items }
            if isinstance(entries, list):
                worktrees: list[Worktree] = []
                for entry in entries:
                    if not isinstance(entry, dict):
                        continue
                    parsed = _worktree_from_wt_entry(entry)
                    if parsed is not None:
                        worktrees.append(parsed)
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
    """Return (is_clean, bad_lines), tolerating allowed prefixes and ephemeral caches.

    Untracked `__pycache__` / `*.pyc` / `.DS_Store` artifacts are ignored: an interpreter run
    without PYTHONDONTWRITEBYTECODE=1 would otherwise fail every admission gate.
    """
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
        if not allowed and is_ephemeral_path(raw_path):
            allowed = True
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


def is_ephemeral_path(raw_path: str) -> bool:
    """True for machine-generated cache artifacts that must never fail a status gate.

    `git status --porcelain` marks an untracked directory with a trailing slash
    (`?? scripts/__pycache__/`), so strip it before matching the patterns.
    """
    candidate: str = raw_path.rstrip("/")
    return any(fnmatch.fnmatch(candidate, pattern) for pattern in EPHEMERAL_STATUS_PATTERNS)


def detect_install_command(cwd: Path | None = None) -> list[str] | None:
    """Frozen-lockfile install command for the project's stack, or None without a lockfile."""
    base: Path = cwd if cwd is not None else Path.cwd()
    for lockfile, command in INSTALL_COMMANDS:
        if (base / lockfile).is_file():
            return list(command)
    return None


def dependency_tree_healthy(cwd: Path | None = None) -> tuple[bool, str]:
    """Probe a copied worktree's Node dependency tree for the copy-ignored failure mode.

    `wt step copy-ignored` copies `node_modules` between worktrees, which can leave the
    top-level symlinks into the pnpm store dangling and the native `.node` bindings unloadable
    — the developer then dies on `Cannot find module '@vitest/utils/helpers'` before writing a
    line. Directory existence cannot see that, so resolve the symlinks for real.
    """
    base: Path = cwd if cwd is not None else Path.cwd()
    node_modules: Path = base / "node_modules"
    if not node_modules.exists():
        if (base / "package.json").is_file():
            return False, "node_modules missing"
        return True, "no node_modules and no package.json"
    checked = 0
    dangling: list[str] = []
    for entry in node_modules.iterdir():
        if not entry.is_symlink():
            continue
        checked += 1
        if not entry.exists():  # broken symlink — target absent
            dangling.append(entry.name)
    if checked == 0:
        return True, "no top-level dependency symlinks"
    if len(dangling) == checked:
        return False, f"all {checked} top-level symlinks dangle (e.g. {', '.join(dangling[:3])})"
    if len(dangling) * 2 > checked:
        return False, f"{len(dangling)}/{checked} top-level symlinks dangle"
    return True, f"{checked - len(dangling)}/{checked} top-level symlinks resolve"


def ensure_dependencies(cwd: Path | None = None, *, force: bool = False) -> tuple[bool, str]:
    """Restore a skeletonized dependency tree in a freshly copied worktree.

    Returns (ok, detail). `ok` is False only when a repair was needed, attempted, and failed.
    A stack with no lockfile, an intact tree, or a missing package manager is a no-op, so
    allocation never fails merely because a machine lacks an optional toolchain.
    """
    base: Path = cwd if cwd is not None else Path.cwd()
    command: list[str] | None = detect_install_command(base)
    if command is None:
        return True, "no lockfile — dependency repair not applicable"
    healthy, detail = (True, "forced") if force else dependency_tree_healthy(base)
    if healthy:
        return True, f"probe passed: {detail}"
    if shutil.which(command[0]) is None:
        print_err(f"dependency repair skipped: {command[0]} not on PATH ({detail})")
        return True, f"{command[0]} not on PATH — skipped"
    result: subprocess.CompletedProcess[str] = run(command, cwd=base)
    if result.returncode != 0:
        print_err(f"dependency repair failed: {' '.join(command)} -> exit {result.returncode}")
        return False, f"{' '.join(command)} failed: {(result.stderr or result.stdout)[:2000]}"
    return True, f"{' '.join(command)} ok ({detail})"


__all__ = [
    "Worktree",
    "current_branch",
    "dependency_tree_healthy",
    "detect_install_command",
    "detect_stack_gate",
    "ensure_clean_worktree",
    "ensure_dependencies",
    "ensure_git_repo",
    "git_status_clean",
    "has_conflict_markers",
    "is_ephemeral_path",
    "print_err",
    "read_gate",
    "run",
    "run_gate",
    "scaffold_wt_config",
    "wt_list",
]
