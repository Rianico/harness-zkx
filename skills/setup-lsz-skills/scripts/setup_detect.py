#!/usr/bin/env python3
"""setup_detect.py — deterministic environment detector and migration engine.

Discovers repo configuration, detects the canonical CLI toolchain, identifies
deprecated `CONTEXT.md` artifacts, and provides idempotent migration paths for
`setup-lsz-skills`. Writes compact YAML to `docs/agents/env.yaml` and renders
Jinja 3.1 templates into `docs/agents/`.

Migration direction is `CONTEXT.md` (deprecated) -> `GLOSSARY.md` (canonical).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

TOOL_SPECS: dict[str, dict[str, str]] = {
    "adr": {
        "purpose": "ADR CLI for architecture decision records",
        "fallback": "manual directory + template",
    },
    "fd": {"purpose": "File discovery (replaces find)", "fallback": "find"},
    "rg": {"purpose": "Content search (replaces grep)", "fallback": "grep"},
    "eza": {"purpose": "Directory tree inspection (replaces ls/tree)", "fallback": "ls / tree"},
    "wt": {"purpose": "Worktree management (replaces git worktree)", "fallback": "git worktree"},
    "uv": {
        "purpose": "Python package/project management (replaces pip/venv)",
        "fallback": "pip / python -m venv",
    },
    "oxlint": {"purpose": "Rust-based ultra-fast linter", "fallback": "ruff / eslint"},
    "oxfmt": {"purpose": "Rust-based code formatter", "fallback": "prettier"},
    "basedpyright": {"purpose": "Type checker for Python", "fallback": "pyright / mypy"},
    "rtk": {
        "purpose": "Token-optimized CLI proxy for shell commands",
        "fallback": "direct command execution",
    },
}

# Deprecated file -> canonical replacement. CONTEXT.md is the legacy name.
STALE_MAP: dict[str, str] = {
    "CONTEXT.md": "GLOSSARY.md",
    "CONTEXT-MAP.md": "GLOSSARY-MAP.md",
}

LSZ_TMP = Path(".lsz") / "tmp"
LSZ_IGNORE_LINES = (".lsz/*", "!.lsz/config.yaml")
ENV_REL = Path("docs") / "agents" / "env.yaml"
TRIAGE_LABELS = ("needs-triage", "needs-info", "ready-for-agent", "ready-for-human", "wontfix")

# RTK (Rust Token Killer) integration. These commands buy marginal compression:
# rewriting or truncating them breaks byte-exact line parsing, so rtk must pass
# them through untouched.
CANONICAL_EXCLUDE_COMMANDS: list[str] = [
    r"^cat\b",
    r"^head\b",
    r"^tail\b",
    r"^grep\b",
    r"^rg\b",
    r"^wc\b",
]

RTK_MIN_VERSION: tuple[int, int, int] = (0, 23, 0)
RTK_AGENTS: tuple[str, ...] = ("pi", "agy", "claude", "codex")
RTK_PROBE_TIMEOUT: float = 15.0
RTK_APPLY_TIMEOUT: float = 120.0

# Runtime signal -> agent, in documented precedence order (pi > agy > claude > codex).
AGENT_ENV_SIGNALS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("pi", ("PI_SESSION_ID", "PI_CODING_AGENT_DIR")),
    ("agy", ("ANTIGRAVITY_AGENT", "ANTIGRAVITY_CONVERSATION_ID")),
    ("claude", ("CLAUDECODE", "CLAUDE_CODE_CHILD_SESSION")),
    ("codex", ("CODEX_SESSION_ID", "CODEX_HOME")),
)

# Exact `rtk init` argv per agent. `--project` drops `-g`, which is the global flag.
RTK_INIT_COMMANDS: dict[str, list[str]] = {
    "pi": ["rtk", "init", "-g", "--agent", "pi"],
    "agy": ["rtk", "init", "--agent", "antigravity"],
    "claude": ["rtk", "init", "-g", "--agent", "claude", "--auto-patch"],
    "codex": ["rtk", "init", "-g", "--codex"],
}


def detect_toolchain(cwd: Path | None = None) -> dict[str, dict[str, Any]]:
    """Check availability of the canonical CLI tools.

    A tool resolves from `PATH` first, then from the target repo's local
    `node_modules/.bin`. Node toolchains pin the Rust linters as
    devDependencies (`oxlint`, `oxfmt`), so they never land on `PATH` and a
    PATH-only probe reports a false gap.
    """
    results: dict[str, dict[str, Any]] = {}
    local_bin = (cwd / "node_modules" / ".bin") if cwd is not None else None
    for name, spec in TOOL_SPECS.items():
        bin_path = shutil.which(name)
        if bin_path is None and local_bin is not None:
            candidate = local_bin / name
            if candidate.is_file() and os.access(candidate, os.X_OK):
                bin_path = str(candidate)
        results[name] = {
            "detected": bin_path is not None,
            "path": bin_path,
            "purpose": spec["purpose"],
            "fallback": spec["fallback"],
        }
    return results


def detect_git_remote(cwd: Path) -> dict[str, Any]:
    """Detect git remote origin URL and classify the hosting provider."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(cwd), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception:
        return {"remote_url": None, "provider": "local"}

    url = proc.stdout.strip()
    if not url:
        return {"remote_url": None, "provider": "local"}
    lowered = url.lower()
    if "github.com" in lowered:
        provider = "github"
    elif "gitlab" in lowered:
        provider = "gitlab"
    else:
        provider = "other"
    return {"remote_url": url, "provider": provider}


def detect_project_name(cwd: Path) -> str:
    """Resolve the project name from git remote, pyproject, package.json, or dir name."""
    remote = detect_git_remote(cwd)["remote_url"]
    if remote:
        tail = remote.rstrip("/").split("/")[-1]
        name = re.sub(r"\.git$", "", tail)
        if name:
            return name

    pyproject = cwd / "pyproject.toml"
    if pyproject.is_file():
        try:
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        name = data.get("project", {}).get("name")
        if isinstance(name, str) and name:
            return name

    package_json = cwd / "package.json"
    if package_json.is_file():
        try:
            data = json.loads(package_json.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        name = data.get("name")
        if isinstance(name, str) and name:
            return name

    return cwd.resolve().name


def detect_stale_files(cwd: Path) -> dict[str, str]:
    """Identify deprecated CONTEXT files that should migrate to GLOSSARY names."""
    found: dict[str, str] = {}
    for old_file, new_file in STALE_MAP.items():
        if (cwd / old_file).exists():
            found[old_file] = new_file
    return found


def _run_capture(
    cmd: list[str],
    timeout: float = RTK_PROBE_TIMEOUT,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str] | None:
    """Run an external command, returning None when it is absent, slow, or unrunnable."""
    try:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=None if cwd is None else str(cwd),
        )
    except Exception:
        return None


def _version_tuple(version: str | None) -> tuple[int, int, int] | None:
    if not version:
        return None
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", version)
    if match is None:
        return None
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def _format_version(version: tuple[int, int, int]) -> str:
    return ".".join(str(part) for part in version)


def detect_active_agent(env: Mapping[str, str] | None = None) -> str | None:
    """Resolve the agent driving this process from its runtime environment.

    A plain developer shell exports none of these signals, so the caller must
    then require an explicit `--agent`.
    """
    source: Mapping[str, str] = os.environ if env is None else env
    for agent, names in AGENT_ENV_SIGNALS:
        if any(source.get(name) for name in names):
            return agent
    return None


def get_rtk_config_path() -> Path:
    """Resolve rtk's user config file for this platform."""
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "rtk" / "config.toml"
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "rtk" / "config.toml"


def _toml_string(value: str) -> str:
    """Render a TOML string, preferring the literal form so regex escapes survive."""
    if "'" not in value:
        return f"'{value}'"
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _toml_string_array(values: list[str]) -> str:
    """Render a TOML array in rtk's own multi-line style."""
    if not values:
        return "[]"
    items = "\n".join(f"    {_toml_string(value)}," for value in values)
    return f"[\n{items}\n]"


def _strip_toml_comment(line: str) -> str:
    """Drop a trailing comment, honoring single- and double-quoted spans."""
    quote: str | None = None
    for index, char in enumerate(line):
        if quote is not None:
            if char == quote:
                quote = None
        elif char in ("'", '"'):
            quote = char
        elif char == "#":
            return line[:index]
    return line


def _bracket_delta(line: str) -> int:
    delta = 0
    quote: str | None = None
    for char in _strip_toml_comment(line):
        if quote is not None:
            if char == quote:
                quote = None
        elif char in ("'", '"'):
            quote = char
        elif char == "[":
            delta += 1
        elif char == "]":
            delta -= 1
    return delta


_TABLE_HEADER = re.compile(r"^\[\s*(?:\"[^\"]*\"|'[^']*'|[A-Za-z0-9_.\-]+)\s*\]$")
_EXCLUDE_KEY = re.compile(r"^([ \t]*)exclude_commands\s*=")
_HOOKS_HEADER = re.compile(r"^\[\s*hooks\s*\]\s*(?:#.*)?$")
# `hooks = {...}` / `hooks.exclude_commands = [...]`: no `[hooks]` table to rewrite in place.
_INLINE_HOOKS = re.compile(r"^\s*hooks\s*[.=]", re.MULTILINE)


def _hook_section_span(lines: list[str]) -> tuple[int, int] | None:
    """Locate the `[hooks]` table: (header index, exclusive end index)."""
    header: int | None = None
    for index, line in enumerate(lines):
        if _HOOKS_HEADER.match(line.strip()):
            header = index
            break
    if header is None:
        return None
    end = len(lines)
    for index in range(header + 1, len(lines)):
        if _TABLE_HEADER.match(lines[index].strip()):
            end = index
            break
    return header, end


def _value_span_end(lines: list[str], start: int, limit: int) -> int:
    """Index of the last line of the assignment at `start` (arrays span lines)."""
    depth = 0
    for index in range(start, limit):
        depth += _bracket_delta(lines[index])
        if depth <= 0:
            return index
    return max(limit - 1, start)


def _rewrite_exclude_commands(text: str, merged: list[str]) -> str | None:
    """Replace only the `[hooks] exclude_commands` value; every other line stays intact.

    Returns None when the file has no `[hooks]` table to rewrite in place, so the
    caller can report the gap instead of appending a duplicate table.
    """
    lines = text.splitlines()
    trailing = "\n" if text.endswith("\n") else ""
    rendered = _toml_string_array(merged)
    span = _hook_section_span(lines)
    if span is None:
        if _INLINE_HOOKS.search(text):
            return None
        lines.extend(["", "[hooks]", f"exclude_commands = {rendered}"])
        return "\n".join(lines) + "\n"
    header, end = span
    for index in range(header + 1, end):
        match = _EXCLUDE_KEY.match(lines[index])
        if match is None:
            continue
        indent = match.group(1)
        block = (indent + f"exclude_commands = {rendered}").splitlines()
        lines[index : _value_span_end(lines, index, end) + 1] = block
        return "\n".join(lines) + trailing
    lines.insert(header + 1, f"exclude_commands = {rendered}")
    return "\n".join(lines) + trailing


def inspect_rtk_config(path: Path | None = None) -> dict[str, Any]:
    """Read the exclude list without mutating anything."""
    config_path = get_rtk_config_path() if path is None else path
    if not config_path.is_file():
        return {
            "exists": False,
            "exclude_commands": [],
            "has_all_canonical": False,
            "missing": list(CANONICAL_EXCLUDE_COMMANDS),
        }
    try:
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return {
            "exists": True,
            "exclude_commands": [],
            "has_all_canonical": False,
            "missing": list(CANONICAL_EXCLUDE_COMMANDS),
            "parse_error": True,
        }
    hooks = data.get("hooks")
    existing: list[str] = []
    if isinstance(hooks, dict):
        raw = hooks.get("exclude_commands")
        if isinstance(raw, list):
            existing = [item for item in raw if isinstance(item, str)]
    missing = [pattern for pattern in CANONICAL_EXCLUDE_COMMANDS if pattern not in existing]
    return {
        "exists": True,
        "exclude_commands": existing,
        "has_all_canonical": not missing,
        "missing": missing,
    }


def _create_rtk_config(config_path: Path, patterns: list[str]) -> bool:
    """Create the config, preferring `rtk config --create` over a hand-written minimal TOML.

    Returns False when the file cannot be seeded with the canonical patterns: a
    caller must never report a creation that did not happen.
    """
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        if shutil.which("rtk") is not None:
            _ = _run_capture(["rtk", "config", "--create"])
        if config_path.is_file():
            current = inspect_rtk_config(config_path)
            if current.get("parse_error"):
                return False
            missing = list(current["missing"])
            if not missing:
                return True
            merged = list(current["exclude_commands"]) + missing
            text = config_path.read_text(encoding="utf-8")
            rewritten = _rewrite_exclude_commands(text, merged)
            if rewritten is None:
                return False
            _ = config_path.write_text(rewritten, encoding="utf-8")
            return True
        body = f"[hooks]\nexclude_commands = {_toml_string_array(patterns)}\n"
        _ = config_path.write_text(body, encoding="utf-8")
        return True
    except OSError:
        return False


def merge_rtk_exclude_commands(path: Path | None = None, dry_run: bool = False) -> dict[str, Any]:
    """Add every missing canonical exclude pattern, preserving the rest of the file.

    Idempotent: a second run reports `added == []` and writes nothing. A refusal
    sets `error`; callers must treat that as a failure, never as success.
    """
    config_path = get_rtk_config_path() if path is None else path
    result: dict[str, Any] = {
        "path": str(config_path),
        "created": False,
        "added": [],
        "dry_run": dry_run,
    }
    if not config_path.is_file():
        result["added"] = list(CANONICAL_EXCLUDE_COMMANDS)
        if dry_run:
            result["created"] = True
            return result
        if not _create_rtk_config(config_path, list(CANONICAL_EXCLUDE_COMMANDS)):
            result["error"] = f"cannot write {config_path}"
            return result
        result["created"] = True
        return result

    current = inspect_rtk_config(config_path)
    if current.get("parse_error"):
        result["error"] = f"cannot parse {config_path}"
        return result
    missing = list(current["missing"])
    if not missing:
        return result
    result["added"] = missing
    if dry_run:
        return result
    merged = list(current["exclude_commands"]) + missing
    text = config_path.read_text(encoding="utf-8")
    rewritten = _rewrite_exclude_commands(text, merged)
    if rewritten is None:
        result["error"] = f"cannot rewrite {config_path}: no [hooks] table"
        return result
    _ = config_path.write_text(rewritten, encoding="utf-8")
    return result


def _hook_target(agent: str, cwd: Path | None = None) -> Path | None:
    """Where `rtk init` records the hook for a given agent."""
    home = Path.home()
    if agent == "pi":
        return home / ".pi" / "agent" / "extensions" / "rtk.ts"
    if agent == "agy":
        return (cwd or Path.cwd()) / ".agents" / "rules" / "antigravity-rtk-rules.md"
    if agent == "claude":
        return home / ".claude" / "settings.json"
    if agent == "codex":
        return home / ".codex" / "RTK.md"
    return None


def _hook_installed(agent: str, cwd: Path | None = None) -> bool:
    target = _hook_target(agent, cwd)
    return target is not None and target.is_file()


def detect_rtk(cwd: Path | None = None, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Read-only RTK state: binary, version gate, active agent, hook, and config."""
    binary = shutil.which("rtk")
    if binary is None and cwd is not None:
        candidate = cwd / "node_modules" / ".bin" / "rtk"
        if candidate.is_file() and os.access(candidate, os.X_OK):
            binary = str(candidate)

    version: str | None = None
    if binary is not None:
        proc = _run_capture([binary, "--version"])
        if proc is not None and proc.returncode == 0:
            match = re.search(r"\d+\.\d+\.\d+", proc.stdout or proc.stderr)
            version = match.group(0) if match else None

    version_tuple = _version_tuple(version)
    active_agent = detect_active_agent(env)
    if active_agent is None:
        hook_installed = any(_hook_installed(agent, cwd) for agent in RTK_AGENTS)
    else:
        hook_installed = _hook_installed(active_agent, cwd)

    config = inspect_rtk_config()
    return {
        "installed": binary is not None,
        "path": binary,
        "version": version,
        "version_ok": version_tuple is not None and version_tuple >= RTK_MIN_VERSION,
        "active_agent": active_agent,
        "hook_installed": hook_installed,
        "exclude_commands": {
            "present": list(config["exclude_commands"]),
            "missing": list(config["missing"]),
        },
    }


def _init_commands(agent: str, project: bool = False) -> list[list[str]]:
    """Exact `rtk init` argv per target agent; `all` runs the four in order."""
    names = list(RTK_AGENTS) if agent == "all" else [agent]
    commands: list[list[str]] = []
    for name in names:
        base = RTK_INIT_COMMANDS[name]
        commands.append([part for part in base if part != "-g"] if project else list(base))
    return commands


def _rtk_check(agent: str, cwd: Path) -> int:
    """Report RTK state. Exit 0 when clean, 1 when an apply is needed."""
    state = detect_rtk(cwd)
    targets = list(RTK_AGENTS) if agent == "all" else [agent]
    hooks = {name: _hook_installed(name, cwd) for name in targets}
    hooks_ok = all(hooks.values())
    preview = merge_rtk_exclude_commands(dry_run=True)
    merge_error = preview.get("error")
    missing = list(preview["added"])

    print(f"rtk check (agent={agent})")
    found = "FOUND" if state["installed"] else "NOT FOUND"
    print(f"  {'installed:':<15}{found} {state['path'] or ''}".rstrip())
    gate = "ok" if state["version_ok"] else f"needs >= {_format_version(RTK_MIN_VERSION)}"
    print(f"  {'version:':<15}{state['version'] or 'unknown'} ({gate})")
    for name, installed in hooks.items():
        status = "installed" if installed else "missing"
        print(f"  {f'hook[{name}]:':<15}{status} {_hook_target(name, cwd)}")
    if merge_error:
        print(f"  {'exclude:':<15}{merge_error}")
    else:
        excludes = "complete" if not missing else f"missing {missing}"
        print(f"  {'exclude:':<15}{excludes} ({preview['path']})")
    clean = bool(
        state["installed"] and state["version_ok"] and hooks_ok and not missing and not merge_error
    )
    print(f"status: {'clean' if clean else 'needs-apply'}")
    if not clean:
        print(f"next:   setup_detect.py rtk --apply --agent {agent}")
    return 0 if clean else 1


def _rtk_apply(agent: str, cwd: Path, dry_run: bool, project: bool) -> int:
    """Install the agent hook and merge the exclude list."""
    commands = _init_commands(agent, project)
    prefix = "[DRY-RUN] " if dry_run else ""
    if dry_run:
        for cmd in commands:
            print(f"{prefix}would run: {' '.join(cmd)}")
        preview = merge_rtk_exclude_commands(dry_run=True)
        if preview.get("error"):
            print(f"{prefix}merge would fail: {preview['error']}")
        else:
            print(f"{prefix}would merge {preview['added']} into {preview['path']}")
        return 0

    failed: list[str] = []
    for cmd in commands:
        proc = _run_capture(cmd, timeout=RTK_APPLY_TIMEOUT, cwd=cwd)
        if proc is None or proc.returncode != 0:
            failed.append(" ".join(cmd))
            continue
        print(f"ran: {' '.join(cmd)}")

    merged = merge_rtk_exclude_commands()
    print(f"exclude_commands: {merged['path']} created={merged['created']} added={merged['added']}")
    if merged.get("error"):
        failed.append(str(merged["error"]))
    if failed:
        print(f"failed: {failed}", file=sys.stderr)
        return 1
    return 0


def _run_rtk_command(args: argparse.Namespace, cwd: Path) -> int:
    """Dispatch `rtk --check` / `rtk --apply`; deterministic, never reads stdin."""
    if not (args.check or args.apply):
        print(
            "usage: setup_detect.py rtk (--check | --apply) [--agent NAME] [--project]",
            file=sys.stderr,
        )
        return 2
    agent = args.agent or detect_active_agent()
    if agent is None:
        print(
            "rtk: no agent detected in this shell — pass --agent {pi,agy,claude,codex,all}",
            file=sys.stderr,
        )
        return 2
    if agent not in (*RTK_AGENTS, "all"):
        print(f"rtk: unknown agent {agent!r}", file=sys.stderr)
        return 2
    if args.check:
        return _rtk_check(agent, cwd)
    return _rtk_apply(
        agent,
        cwd,
        dry_run=args.dry_run,
        project=args.project,
    )


def detect_environment(cwd: Path) -> dict[str, Any]:
    """Inspect the full environment state."""
    agents_md = cwd / "AGENTS.md"
    claude_md = cwd / "CLAUDE.md"
    adr_dir = cwd / "docs" / "adr"
    docs_agents = cwd / "docs" / "agents"

    existing_docs_agents: list[str] = []
    if docs_agents.is_dir():
        existing_docs_agents = sorted(
            f.name for f in docs_agents.iterdir() if f.is_file() and f.suffix == ".md"
        )

    steering = "AGENTS.md" if agents_md.exists() else ("CLAUDE.md" if claude_md.exists() else None)
    git = detect_git_remote(cwd)

    return {
        "cwd": str(cwd.resolve()),
        "project_name": detect_project_name(cwd),
        "git": git,
        "provider": git["provider"],
        "steering_file": steering,
        "has_agents_md": agents_md.exists(),
        "has_claude_md": claude_md.exists(),
        "has_context_md": (cwd / "CONTEXT.md").exists(),
        "has_context_map": (cwd / "CONTEXT-MAP.md").exists(),
        "has_glossary_md": (cwd / "GLOSSARY.md").exists(),
        "has_adr_dir": adr_dir.is_dir(),
        "existing_docs_agents": existing_docs_agents,
        "stale_files": detect_stale_files(cwd),
        "toolchain": detect_toolchain(cwd),
        "rtk": detect_rtk(cwd),
    }


def ensure_lsz_workspace(cwd: Path, dry_run: bool = False) -> dict[str, Any]:
    """Create `.lsz/tmp/` and ensure `.gitignore` keeps `.lsz/*` private but config visible."""
    tmp_dir = cwd / LSZ_TMP
    gitignore = cwd / ".gitignore"

    created_dir = False
    if not tmp_dir.is_dir():
        created_dir = not dry_run
        if not dry_run:
            tmp_dir.mkdir(parents=True, exist_ok=True)

    added_lines: list[str] = []
    existing: list[str] = []
    if gitignore.is_file():
        existing = gitignore.read_text(encoding="utf-8").splitlines()
    missing = [line for line in LSZ_IGNORE_LINES if line not in existing]

    if missing and not dry_run:
        header = "" if (not existing or existing[-1] == "") else "\n"
        with gitignore.open("a", encoding="utf-8") as fh:
            _ = fh.write(header + "\n".join(missing) + "\n")
        added_lines = missing

    return {
        "tmp_dir": str(tmp_dir.relative_to(cwd)),
        "created_dir": created_dir,
        "added_ignore_lines": added_lines,
        "gitignore_ok": not missing,
        "dry_run": dry_run,
    }


def _compact_dump(data: dict[str, Any]) -> str:
    return yaml.safe_dump(
        data,
        default_flow_style=False,
        sort_keys=False,
        width=1000,
        allow_unicode=True,
    )


def build_env_document(state: dict[str, Any]) -> dict[str, Any]:
    """Shape the detection state into the compact env.yaml document."""
    toolchain = {
        name: {
            "detected": tool["detected"],
            "fallback": tool["fallback"],
        }
        for name, tool in state["toolchain"].items()
    }
    rtk_state = state.get("rtk") or {}
    rtk_document = {
        "installed": bool(rtk_state.get("installed", False)),
        "version": rtk_state.get("version"),
    }
    return {
        "project": state["project_name"],
        "provider": state["provider"],
        "remote_url": state["git"]["remote_url"],
        "steering_file": state["steering_file"],
        "domain_layout": {
            "glossary": "GLOSSARY.md",
            "glossary_map": "GLOSSARY-MAP.md",
            "adr_dir": "docs/adr",
            "stale_files": state["stale_files"],
        },
        "runtime": {"tmp": str(LSZ_TMP)},
        "toolchain": toolchain,
        "rtk": rtk_document,
    }


def write_env_yaml(cwd: Path, state: dict[str, Any], dry_run: bool = False) -> dict[str, Any]:
    """Write compact YAML to `docs/agents/env.yaml`. No JSON representation."""
    out_path = cwd / ENV_REL
    document = build_env_document(state)
    text = _compact_dump(document)

    if not dry_run:
        _ = out_path.parent.mkdir(parents=True, exist_ok=True)
        _ = out_path.write_text(text, encoding="utf-8")

    return {"path": str(ENV_REL), "written": not dry_run, "content": text, "dry_run": dry_run}


def _merge_paths(cwd: Path, old_name: str) -> Path:
    """Where to stage a deprecated file that collides with an existing canonical file."""
    return cwd / LSZ_TMP / f"{old_name}.pending-merge"


def execute_migration(
    cwd: Path,
    dry_run: bool = False,
    init_adr: bool = True,
) -> dict[str, Any]:
    """Migrate deprecated `CONTEXT.md` files to `GLOSSARY.md`.

    A straight rename runs only when the canonical target is absent. When both
    exist, the deprecated file is staged under `.lsz/tmp/` for a semantic merge
    and reported for interactive resolution; nothing is clobbered. Optionally
    creates the `docs/adr/` directory when it is missing.
    """
    stale = detect_stale_files(cwd)
    migrated: list[dict[str, str]] = []
    merge_required: list[dict[str, str]] = []

    for old_name, new_name in stale.items():
        old_path = cwd / old_name
        new_path = cwd / new_name
        if not old_path.exists():
            continue

        if new_path.exists():
            staged = _merge_paths(cwd, old_name)
            if not dry_run:
                _ = staged.parent.mkdir(parents=True, exist_ok=True)
                _ = shutil.copy2(str(old_path), str(staged))
            merge_required.append(
                {
                    "source": old_name,
                    "target": new_name,
                    "staged_as": str(staged.relative_to(cwd)),
                    "reason": f"both {old_name} and {new_name} exist; semantic merge needed",
                }
            )
            continue

        if not dry_run:
            _ = shutil.move(str(old_path), str(new_path))
        migrated.append({"source": old_name, "target": new_name})

    adr = _init_adr_dir(cwd, dry_run=dry_run, enabled=init_adr)

    return {"dry_run": dry_run, "migrated": migrated, "merge_required": merge_required, "adr": adr}


def _init_adr_dir(cwd: Path, dry_run: bool, enabled: bool) -> dict[str, Any]:
    adr_dir = cwd / "docs" / "adr"
    if not enabled:
        return {"enabled": False, "created": False}
    created = False
    if not adr_dir.is_dir():
        created = not dry_run
        if not dry_run:
            adr_dir.mkdir(parents=True, exist_ok=True)
    return {
        "enabled": True,
        "created": created,
        "exists": adr_dir.is_dir(),
        "adr_cli": shutil.which("adr") is not None,
    }


def build_template_context(state: dict[str, Any]) -> dict[str, Any]:
    """Assemble the variables every `.j2` template may reference (StrictUndefined-safe)."""
    return {
        "project": state["project_name"],
        "provider": state["provider"],
        "remote_url": state["git"]["remote_url"],
        "steering_file": state["steering_file"] or "AGENTS.md",
        "glossary": "GLOSSARY.md",
        "glossary_map": "GLOSSARY-MAP.md",
        "adr_dir": "docs/adr",
        "has_context_map": state["has_context_map"],
        "toolchain": state["toolchain"],
        "triage_labels": list(TRIAGE_LABELS),
        "rtk": state.get("rtk") or {},
    }


def render_docs(
    cwd: Path,
    state: dict[str, Any],
    templates_dir: Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Render the `.j2` templates into `docs/agents/` with the canonical Jinja 3.1 environment."""
    from jinja2 import Environment, FileSystemLoader, StrictUndefined

    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        undefined=StrictUndefined,
    )
    ctx = build_template_context(state)
    out_dir = cwd / "docs" / "agents"

    provider = ctx["provider"]
    if provider not in ("github", "gitlab", "local"):
        provider = "local"
    plan = [
        ("domain.md.j2", "domain.md"),
        ("toolchain.md.j2", "toolchain.md"),
        (f"issue-tracker-{provider}.md.j2", "issue-tracker.md"),
        ("triage-labels.md.j2", "triage-labels.md"),
    ]

    rendered: list[str] = []
    for template_name, out_name in plan:
        text = env.get_template(template_name).render(**ctx)
        rendered.append(out_name)
        if not dry_run:
            _ = out_dir.mkdir(parents=True, exist_ok=True)
            _ = (out_dir / out_name).write_text(text, encoding="utf-8")

    return {"dry_run": dry_run, "rendered": rendered, "provider": provider}


def main() -> int:
    parser = argparse.ArgumentParser(description="setup-lsz-skills environment detector & migrator")
    _ = parser.add_argument(
        "--cwd", type=Path, default=Path.cwd(), help="Target repository directory"
    )
    _ = parser.add_argument(
        "--templates",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "templates",
        help="Directory holding the .j2 templates",
    )
    sub = parser.add_subparsers(dest="command")

    detect_p = sub.add_parser("detect", help="Inspect the environment")
    _ = detect_p.add_argument("--json", action="store_true", help="Print state as JSON")
    _ = detect_p.add_argument("--write-env", action="store_true", help="Write docs/agents/env.yaml")
    _ = detect_p.add_argument("--dry-run", action="store_true", help="Do not write env.yaml")

    migrate_p = sub.add_parser("migrate", help="Migrate CONTEXT.md -> GLOSSARY.md")
    _ = migrate_p.add_argument("--dry-run", action="store_true", help="Preview migration")
    _ = migrate_p.add_argument("--no-adr", action="store_true", help="Skip docs/adr initialization")

    workspace_p = sub.add_parser("workspace", help="Create .lsz/tmp and update .gitignore")
    _ = workspace_p.add_argument("--dry-run", action="store_true", help="Preview workspace changes")

    render_p = sub.add_parser("render", help="Render .j2 templates into docs/agents/")
    _ = render_p.add_argument("--dry-run", action="store_true", help="Preview rendering")

    rtk_p = sub.add_parser("rtk", help="Inspect or apply the RTK integration")
    rtk_mode = rtk_p.add_mutually_exclusive_group()
    _ = rtk_mode.add_argument(
        "--check", action="store_true", help="Report RTK state; exit 1 when apply is needed"
    )
    _ = rtk_mode.add_argument(
        "--apply", action="store_true", help="Install the agent hook and merge exclude patterns"
    )
    _ = rtk_p.add_argument(
        "--agent",
        choices=(*RTK_AGENTS, "all"),
        default=None,
        help="Target agent (defaults to runtime detection)",
    )
    _ = rtk_p.add_argument(
        "--project", action="store_true", help="Install the hook for this project, not globally"
    )
    _ = rtk_p.add_argument(
        "--dry-run", action="store_true", help="Print the intent without writing anything"
    )

    args = parser.parse_args()
    target_cwd = args.cwd.resolve()
    command = args.command or "detect"
    if command == "rtk":
        return _run_rtk_command(args, target_cwd)

    state = detect_environment(target_cwd)

    if command == "detect":
        if args.write_env:
            result = write_env_yaml(target_cwd, state, dry_run=args.dry_run)
            print(f"{'[DRY-RUN] ' if args.dry_run else ''}wrote {result['path']}")
        elif args.json:
            print(json.dumps(state, indent=2))
        else:
            print(_format_report(state))
        return 0

    if command == "workspace":
        result = ensure_lsz_workspace(target_cwd, dry_run=getattr(args, "dry_run", False))
        prefix = "[DRY-RUN] " if args.dry_run else ""
        print(
            f"{prefix}tmp_dir={result['tmp_dir']} created={result['created_dir']} "
            f"added={result['added_ignore_lines']}"
        )
        return 0

    if command == "migrate":
        result = execute_migration(target_cwd, dry_run=args.dry_run, init_adr=not args.no_adr)
        prefix = "[DRY-RUN] " if args.dry_run else ""
        for item in result["migrated"]:
            print(f"{prefix}renamed {item['source']} -> {item['target']}")
        for item in result["merge_required"]:
            print(
                f"{prefix}merge needed: {item['source']} vs {item['target']} "
                f"(staged {item['staged_as']})"
            )
        if not result["migrated"] and not result["merge_required"]:
            print(f"{prefix}no deprecated CONTEXT files needed migration.")
        return 0

    if command == "render":
        result = render_docs(target_cwd, state, args.templates, dry_run=args.dry_run)
        prefix = "[DRY-RUN] " if args.dry_run else ""
        print(f"{prefix}rendered {result['rendered']} (provider={result['provider']})")
        return 0

    return 0


def _format_report(state: dict[str, Any]) -> str:
    lines = [
        f"Project:         {state['project_name']}",
        f"Repository Root: {state['cwd']}",
        f"Git Remote:      {state['git']['remote_url']} (Provider: {state['provider']})",
        f"Steering File:   {state['steering_file'] or 'None found'}",
        "Domain:          GLOSSARY.md (canonical); CONTEXT.md deprecated",
        f"ADR Directory:   {'docs/adr (present)' if state['has_adr_dir'] else 'docs/adr (missing)'}",
    ]
    if state["stale_files"]:
        pairs = ", ".join(f"{k} -> {v}" for k, v in state["stale_files"].items())
        lines.append(f"Stale Files:     {pairs}")
    lines.append("")
    lines.append("Toolchain Availability:")
    for tool, details in state["toolchain"].items():
        if details["detected"] and "/node_modules/.bin/" in (details["path"] or ""):
            status = "FOUND (local)"
        else:
            status = "FOUND" if details["detected"] else "NOT FOUND"
        lines.append(
            f"  {tool:<14} {status:<10} ({details['purpose']}) fallback: {details['fallback']}"
        )
    rtk_state = state.get("rtk") or {}
    if rtk_state:
        rtk_found = "FOUND" if rtk_state.get("installed") else "NOT FOUND"
        hook = "installed" if rtk_state.get("hook_installed") else "missing"
        lines.append(
            f"  {'rtk':<14} {rtk_found:<10} (Token-optimized CLI proxy for shell commands) "
            f"version={rtk_state.get('version')} agent={rtk_state.get('active_agent')} hook={hook}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
