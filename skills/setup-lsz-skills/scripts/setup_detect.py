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

    args = parser.parse_args()
    target_cwd = args.cwd.resolve()
    command = args.command or "detect"
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
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
