#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["rich>=13.0.0"]
# ///
"""skill-stocktake CLI — unified inventory and summary tool.

Usage:
    uv run stocktake.py scan [--output json|rich|markdown]
    uv run stocktake.py diff [--results PATH]
    uv run stocktake.py overview [--width N]
    uv run stocktake.py summary [--results PATH] [--output rich|markdown|json]
    uv run stocktake.py save [--results PATH] < eval.json
    uv run stocktake.py merge-chunks [--results PATH] [--clean]

Commands:
    scan          Phase 1: Inventory all skills
    diff          Quick Scan: Find changed skills since last run
    overview      Quick overview with usage stats (today, 7d, 30d) - rich output only
    summary       Phase 3: Display results table
    save          Merge evaluation results into results.json
    merge-chunks  Merge chunked evaluation files from .tmp/ directory
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path

# Add lib to path for tz import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "lib"))
from rich.box import HORIZONTALS, ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from tz import local_tz, to_local_display

# Defaults - cache Path.home() to avoid repeated syscalls
HOME = Path.home()
DEFAULT_GLOBAL_DIR = HOME / ".claude" / "skills"
DEFAULT_OBSERVATIONS_DIR = HOME / ".claude" / "lsz" / "homunculus"
DEFAULT_RESULTS = HOME / ".claude" / "lsz" / "skill-stocktake" / "results.json"
DEFAULT_TMP_DIR = HOME / ".claude" / "lsz" / "skill-stocktake" / ".tmp"
HOME_STR = str(HOME)

# Let Rich auto-detect terminal width
console = Console()


# Verdict enum for type-safe verdict strings
class Verdict(StrEnum):
    """Verdict categories for skill evaluations."""

    KEEP = "Keep"
    IMPROVE = "Improve"
    UPDATE = "Update"
    MERGE = "Merge"
    RETIRE = "Retire"


class OutputFormat(StrEnum):
    """Output format options for CLI commands."""

    JSON = "json"
    RICH = "rich"
    MARKDOWN = "markdown"


class GroupBy(StrEnum):
    """Grouping options for summary output."""

    VERDICT = "verdict"
    SKILL = "skill"


# Verdict color mapping for rich output
VERDICT_COLORS: dict[Verdict, str] = {
    Verdict.KEEP: "green",
    Verdict.IMPROVE: "yellow",
    Verdict.UPDATE: "blue",
    Verdict.MERGE: "magenta",
    Verdict.RETIRE: "red",
}


# Shared utilities


def extract_frontmatter(content: str) -> dict[str, str]:
    """Extract YAML frontmatter from markdown content."""
    result = {}
    lines = content.split("\n")
    in_frontmatter = 0

    for line in lines:
        stripped = line.strip()
        if stripped == "---":
            in_frontmatter += 1
            if in_frontmatter > 1:
                break
            continue

        if in_frontmatter != 1:
            continue

        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            result[key] = value

    return result


def get_mtime_utc(path: Path) -> str:
    """Get file modification time as ISO 8601 UTC string."""
    mtime = path.stat().st_mtime
    dt = datetime.fromtimestamp(mtime, tz=UTC)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_skills(skills: dict | list) -> list[dict]:
    """Normalize skills to list format.

    Handles both dict format (path -> skill_data) and list format.
    Dict format is converted to list with path included in each item.
    """
    if isinstance(skills, list):
        return skills
    return [{"path": k, **v} for k, v in skills.items()]


def get_skill_name(skill: dict) -> str:
    """Extract skill name from skill record, falling back to path parent or stem.

    For SKILL.md files, uses the parent directory name.
    For other files, uses the file stem.
    """
    name = skill.get("name", "")
    if name:
        return name
    path = skill.get("path", "")
    if not path:
        return ""
    p = Path(path)
    return p.parent.name if p.name == "SKILL.md" else p.stem


def truncate_text(text: str, width: int, ellipsis: str = "…") -> str:
    """Truncate text to width, adding ellipsis if truncated."""
    if len(text) <= width:
        return text
    return text[: width - len(ellipsis)] + ellipsis


def get_observation_files(observations_dir: Path) -> list[Path]:
    """Get all observation files (global + project-specific)."""
    files = []

    global_file = observations_dir / "observations.jsonl"
    if global_file.exists():
        files.append(global_file)

    projects_dir = observations_dir / "projects"
    if projects_dir.exists():
        for project_dir in projects_dir.iterdir():
            if project_dir.is_dir():
                obs_file = project_dir / "observations.jsonl"
                if obs_file.exists():
                    files.append(obs_file)

    return files


def count_read_observations(
    observations_files: list[Path],
) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
    """Count Read tool observations per file path in single pass.

    Returns tuple of (counts_1d, counts_7d, counts_30d) for use in scan operations.
    """
    now = datetime.now(local_tz())
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    cutoff_7d = now - timedelta(days=7)
    cutoff_30d = now - timedelta(days=30)
    today_start_str = today_start.strftime("%Y-%m-%dT%H:%M:%SZ")
    cutoff_7d_str = cutoff_7d.strftime("%Y-%m-%dT%H:%M:%SZ")
    cutoff_30d_str = cutoff_30d.strftime("%Y-%m-%dT%H:%M:%SZ")

    counts_1d: dict[str, int] = {}
    counts_7d: dict[str, int] = {}
    counts_30d: dict[str, int] = {}

    for obs_file in observations_files:
        try:
            with open(obs_file) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obs = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if obs.get("tool") != "Read":
                        continue

                    timestamp = obs.get("timestamp", "")
                    file_path = obs.get("input", {}).get("file_path")
                    if not file_path:
                        continue

                    # Single pass: check all windows
                    if timestamp >= today_start_str:
                        counts_1d[file_path] = counts_1d.get(file_path, 0) + 1
                    if timestamp >= cutoff_7d_str:
                        counts_7d[file_path] = counts_7d.get(file_path, 0) + 1
                    if timestamp >= cutoff_30d_str:
                        counts_30d[file_path] = counts_30d.get(file_path, 0) + 1
        except OSError:
            continue

    return counts_1d, counts_7d, counts_30d


def _format_path_with_tilde(path: Path | str) -> str:
    """Format path with tilde prefix if under home directory."""
    path_str = str(path) if isinstance(path, str) else str(path)
    if path_str.startswith(HOME_STR):
        return "~" + path_str[len(HOME_STR) :]
    return path_str


def _walk_skills_dir(skills_dir: Path, followlinks: bool = True) -> Generator[Path, None, None]:
    """Walk skills directory and yield all .md files."""
    for root, _, files in os.walk(skills_dir, followlinks=followlinks):
        root_path = Path(root)
        for filename in files:
            if filename.endswith(".md"):
                yield root_path / filename


def scan_skills_dir(
    skills_dir: Path,
    use_1d: dict[str, int],
    use_7d: dict[str, int],
    use_30d: dict[str, int],
) -> list[dict]:
    """Scan a skills directory and return list of skill metadata."""
    skills = []

    if not skills_dir.exists():
        return skills

    for md_file in _walk_skills_dir(skills_dir):
        try:
            content = md_file.read_text()
        except OSError:
            continue

        frontmatter = extract_frontmatter(content)
        path_str = _format_path_with_tilde(md_file)

        # Compute lookup key once: prefer resolved path for symlinks
        key = str(md_file.resolve()) if md_file.is_symlink() else str(md_file)
        # Fallback to direct path if key not found
        alt_key = str(md_file) if key != str(md_file) else None
        file_path_1d = use_1d.get(key, use_1d.get(alt_key, 0) if alt_key else 0)
        file_path_7d = use_7d.get(key, use_7d.get(alt_key, 0) if alt_key else 0)
        file_path_30d = use_30d.get(key, use_30d.get(alt_key, 0) if alt_key else 0)

        skills.append(
            {
                "path": path_str,
                "name": frontmatter.get("name", ""),
                "description": frontmatter.get("description", ""),
                "use_1d": file_path_1d,
                "use_7d": file_path_7d,
                "use_30d": file_path_30d,
                "mtime": get_mtime_utc(md_file),
            }
        )

    skills.sort(key=lambda s: s["path"])
    return skills


# Command: scan


def cmd_scan(args: argparse.Namespace) -> int:
    """Phase 1: Inventory all skills."""
    global_dir = args.global_dir or DEFAULT_GLOBAL_DIR
    observations_dir = args.observations_dir or DEFAULT_OBSERVATIONS_DIR
    project_dir = args.project_dir

    if project_dir is None:
        project_dir = Path.cwd() / ".claude" / "skills"

    # Get observation counts (single pass returns all windows)
    obs_files = get_observation_files(observations_dir)
    use_1d, use_7d, use_30d = count_read_observations(obs_files)

    # Scan directories
    global_skills = scan_skills_dir(global_dir, use_1d, use_7d, use_30d)
    project_skills = (
        scan_skills_dir(project_dir, use_1d, use_7d, use_30d) if project_dir.exists() else []
    )

    all_skills = global_skills + project_skills

    data = {
        "scan_summary": {
            "global": {
                "found": global_dir.exists(),
                "count": len(global_skills),
            },
            "project": {
                "found": project_dir.exists(),
                "path": str(project_dir) if project_dir.exists() else "",
                "count": len(project_skills),
            },
        },
        "skills": all_skills,
    }

    if args.output == "json":
        print(json.dumps(data, indent=2))
    elif args.output == "markdown":
        print(format_scan_markdown(data))
    else:
        # Use width override if provided, otherwise let Rich auto-detect
        render_console = Console(width=args.width) if args.width else console
        render_scan_rich(data, render_console)

    return 0


def format_scan_markdown(data: dict) -> str:
    """Format scan as markdown."""
    lines = []
    summary = data["scan_summary"]

    lines.append("**Scanning:**")
    global_info = summary["global"]
    if global_info["found"]:
        lines.append(f"  ✓ ~/.claude/skills/ ({global_info['count']} files)")
    else:
        lines.append("  ✗ ~/.claude/skills/ (not found)")

    project_info = summary["project"]
    if project_info["found"]:
        lines.append(f"  ✓ {project_info['path']} ({project_info['count']} files)")
    else:
        lines.append("  ✗ project skills (not found)")

    lines.append("")
    lines.append("| Skill | 7d | 30d | Description |")
    lines.append("|-------|-----|------|-------------|")

    for skill in data["skills"]:
        name = get_skill_name(skill)
        desc = truncate_text(skill["description"], 57, "...")
        desc = desc.replace("|", "\\|")
        lines.append(f"| {name} | {skill['use_7d']} | {skill['use_30d']} | {desc} |")

    return "\n".join(lines)


def render_scan_rich(data: dict, render_console: Console | None = None) -> None:
    """Render scan results with rich tables."""
    con = render_console or console
    # Calculate description column width: total - (Skill:15 + 7d:4 + 30d:5 + borders:8)
    desc_width = max(40, con.width - 32)

    summary = data["scan_summary"]

    # Scan summary panel
    project_status = "green" if summary["project"]["found"] else "red"
    project_check = "✓" if summary["project"]["found"] else "✗"
    con.print(
        Panel.fit(
            f"[green]✓[/green] ~/.claude/skills/ ({summary['global']['count']} files)\n"
            f"[{project_status}]{project_check}[/] "
            f"{summary['project']['path'] or 'project skills'} ({summary['project']['count']} files)",
            title="[bold]Scanning[/bold]",
        )
    )

    # Skills table with HORIZONTALS style and row separators
    table = Table(
        title=f"[bold]Inventory[/bold] ({len(data['skills'])} skills)",
        box=HORIZONTALS,
        show_lines=True,
    )
    table.add_column("Skill", style="cyan", no_wrap=True, width=15)
    table.add_column("7d", justify="right", style="green", no_wrap=True, width=4)
    table.add_column("30d", justify="right", style="yellow", no_wrap=True, width=5)
    table.add_column("Description", style="dim", width=desc_width)

    for skill in data["skills"]:
        name = get_skill_name(skill)
        desc = truncate_text(skill["description"], desc_width)
        table.add_row(name, str(skill["use_7d"]), str(skill["use_30d"]), desc)

    con.print(table)


# Command: diff


def cmd_diff(args: argparse.Namespace) -> int:
    """Quick Scan: Find changed skills since last run."""
    results_path = args.results or DEFAULT_RESULTS
    project_dir = args.project_dir or Path.cwd() / ".claude" / "skills"
    global_dir = args.global_dir or DEFAULT_GLOBAL_DIR

    if not results_path.exists():
        console.print(f"[red]Error:[/red] Results file not found: {results_path}")
        console.print("Run a full stocktake first to create results.json")
        return 1

    with open(results_path) as f:
        results = json.load(f)

    evaluated_at = results.get("evaluated_at", "")
    if not evaluated_at:
        console.print("[red]Error:[/red] No evaluated_at in results.json")
        return 1

    # Handle both list and dict formats for skills
    skills_data = results.get("skills", [])
    if isinstance(skills_data, list):
        known_paths = {s.get("path", "") for s in skills_data}
    else:
        known_paths = set(skills_data.keys())
    changed = []

    # Check global skills
    if global_dir.exists():
        changed.extend(find_changed_skills(global_dir, evaluated_at, known_paths))

    # Check project skills
    if project_dir.exists():
        changed.extend(find_changed_skills(project_dir, evaluated_at, known_paths))

    if args.output == "json":
        print(json.dumps(changed, indent=2))
    else:
        render_diff_rich(changed, evaluated_at)

    return 0


def find_changed_skills(skills_dir: Path, evaluated_at: str, known_paths: set[str]) -> list[dict]:
    """Find skills that changed since last evaluation."""
    changed = []

    for md_file in _walk_skills_dir(skills_dir):
        mtime = get_mtime_utc(md_file)
        path_str = _format_path_with_tilde(md_file)

        # Extract skill name from path
        skill_name = md_file.parent.name if md_file.name == "SKILL.md" else md_file.stem

        is_new = skill_name not in known_paths

        if is_new or mtime > evaluated_at:
            changed.append(
                {
                    "path": path_str,
                    "name": skill_name,
                    "mtime": mtime,
                    "is_new": is_new,
                }
            )

    return changed


def render_diff_rich(changed: list[dict], evaluated_at: str) -> None:
    """Render diff results with rich."""
    if not changed:
        console.print(
            Panel.fit(
                f"No changes since {to_local_display(evaluated_at)}",
                title="Quick Scan",
            )
        )
        return

    console.print(
        Panel.fit(
            f"Last evaluated: {to_local_display(evaluated_at)}",
            title="Quick Scan",
        )
    )

    table = Table(title=f"Changed Skills ({len(changed)})", box=HORIZONTALS, show_lines=True)
    table.add_column("Skill", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("Modified", no_wrap=True)

    for item in sorted(changed, key=lambda x: x["name"]):
        status = "NEW" if item["is_new"] else "MODIFIED"
        local_mtime = to_local_display(item["mtime"])
        table.add_row(item["name"], status, local_mtime)

    console.print(table)


# Command: overview


def cmd_overview(args: argparse.Namespace) -> int:
    """Quick overview of skills with usage stats."""
    global_dir = args.global_dir or DEFAULT_GLOBAL_DIR
    observations_dir = args.observations_dir or DEFAULT_OBSERVATIONS_DIR
    project_dir = args.project_dir or Path.cwd() / ".claude" / "skills"

    # Get observation counts
    obs_files = get_observation_files(observations_dir)
    use_1d, use_7d, use_30d = count_read_observations(obs_files)

    # Scan directories
    global_skills = scan_skills_dir(global_dir, use_1d, use_7d, use_30d)
    project_skills = (
        scan_skills_dir(project_dir, use_1d, use_7d, use_30d) if project_dir.exists() else []
    )

    # Filter to only main SKILL.md files (not references)
    all_skills = [s for s in global_skills + project_skills if s["path"].endswith("/SKILL.md")]
    # Sort by 7d usage descending, then by name for ties
    all_skills.sort(
        key=lambda s: (-s.get("use_7d", 0), s.get("name") or Path(s.get("path", "")).stem)
    )

    render_console = Console(width=args.width) if args.width else console
    render_overview_rich(all_skills, render_console)

    return 0


def render_overview_rich(skills: list[dict], render_console: Console | None = None) -> None:
    """Render overview table with usage stats."""
    con = render_console or console
    # Calculate description column width: total - (Skill:20 + 1d:4 + 7d:4 + 30d:5 + borders:8)
    desc_width = max(40, con.width - 41)

    # Summary counts
    total = len(skills)
    used_1d = sum(1 for s in skills if s.get("use_1d", 0) > 0)

    summary_table = Table(show_header=False, box=ROUNDED)
    summary_table.add_column("Metric", style="bold")
    summary_table.add_column("Value", justify="right")
    summary_table.add_row("Total skills", str(total))
    summary_table.add_row("Used today", str(used_1d))
    con.print(summary_table)

    # Main table
    table = Table(title="[bold]Skills Overview[/bold]", box=HORIZONTALS, show_lines=True)
    table.add_column("Skill", style="cyan", no_wrap=True, width=20)
    table.add_column("1d", justify="right", style="green", no_wrap=True, width=4)
    table.add_column("7d", justify="right", style="green", no_wrap=True, width=4)
    table.add_column("30d", justify="right", style="yellow", no_wrap=True, width=5)
    table.add_column("Description", style="dim", width=desc_width)

    for skill in skills:
        name = get_skill_name(skill)
        desc = truncate_text(skill.get("description", ""), desc_width)
        table.add_row(
            name,
            str(skill.get("use_1d", 0)),
            str(skill.get("use_7d", 0)),
            str(skill.get("use_30d", 0)),
            desc,
        )

    con.print(table)


# Command: summary


def cmd_summary(args: argparse.Namespace) -> int:
    """Phase 3: Display results table."""
    results_path = args.results or DEFAULT_RESULTS

    if not results_path.exists():
        console.print(f"[red]Error:[/red] Results file not found: {results_path}")
        return 1

    with open(results_path) as f:
        data = json.load(f)

    if args.output == "json":
        print(format_summary_json(data))
    elif args.output == "markdown":
        print(format_summary_markdown(data, args.group_by))
    else:
        # Use width override if provided, otherwise let Rich auto-detect
        render_console = Console(width=args.width) if args.width else console
        render_summary_rich(data, args.group_by, render_console)

    return 0


def format_summary_markdown(data: dict, group_by: str) -> str:
    """Format results as markdown table."""
    lines = []

    evaluated_at = data.get("evaluated_at", "unknown")
    mode = data.get("mode", "unknown")
    progress = data.get("batch_progress", {})
    status = progress.get("status", "unknown")

    lines.append(f"**Evaluated:** {evaluated_at}")
    lines.append(f"**Mode:** {mode}")
    lines.append(f"**Status:** {status}")
    lines.append("")

    skills = normalize_skills(data.get("skills", []))

    if group_by == "verdict":
        by_verdict: dict[str, list[dict]] = defaultdict(list)
        for skill in skills:
            verdict = skill.get("verdict", "Unknown")
            by_verdict[verdict].append(skill)

        for verdict in Verdict:
            if verdict.value not in by_verdict:
                continue

            items = by_verdict[verdict]
            lines.append(f"### {verdict} ({len(items)})")
            lines.append("")
            lines.append("| Skill | 7d | Reason |")
            lines.append("|-------|-----|--------|")

            for skill in sorted(items, key=lambda x: get_skill_name(x)):
                name = get_skill_name(skill)
                use_7d = skill.get("use_7d", 0)
                reason = truncate_text(skill.get("reason", ""), 77, "...")
                reason = reason.replace("|", "\\|")
                lines.append(f"| {name} | {use_7d} | {reason} |")

            lines.append("")
    else:
        lines.append("| Skill | 7d | Verdict | Reason |")
        lines.append("|-------|-----|---------|--------|")

        for skill in sorted(skills, key=lambda x: get_skill_name(x)):
            name = get_skill_name(skill)
            use_7d = skill.get("use_7d", 0)
            verdict = skill.get("verdict", "Unknown")
            reason = truncate_text(skill.get("reason", ""), 57, "...")
            reason = reason.replace("|", "\\|")
            lines.append(f"| {name} | {use_7d} | {verdict} | {reason} |")

    # Summary counts
    lines.append("### Summary")
    lines.append("")
    lines.append("| Verdict | Count |")
    lines.append("|---------|-------|")

    counts: dict[str, int] = defaultdict(int)
    for skill in skills:
        counts[skill.get("verdict", "Unknown")] += 1

    for verdict in Verdict:
        lines.append(f"| {verdict.value} | {counts.get(verdict.value, 0)} |")

    return "\n".join(lines)


def format_summary_json(data: dict) -> str:
    """Format results as compact JSON."""
    skills = normalize_skills(data.get("skills", []))

    summary = {
        "evaluated_at": data.get("evaluated_at"),
        "mode": data.get("mode"),
        "total": len(skills),
        "by_verdict": defaultdict(list),
        "skills": [],
    }

    for skill in sorted(skills, key=lambda x: get_skill_name(x)):
        name = get_skill_name(skill)
        summary["skills"].append(
            {
                "name": name,
                "verdict": skill.get("verdict"),
                "use_7d": skill.get("use_7d", 0),
                "reason": skill.get("reason", "")[:100],
            }
        )
        summary["by_verdict"][skill.get("verdict", "Unknown")].append(name)

    summary["by_verdict"] = dict(summary["by_verdict"])
    return json.dumps(summary, indent=2)


def render_summary_rich(data: dict, group_by: str, render_console: Console | None = None) -> None:
    """Render results with rich tables."""
    con = render_console or console
    # Calculate reason column width: total - (Skill:15 + 7d:4 + 30d:5 + borders:8)
    reason_width = max(40, con.width - 32)

    evaluated_at = data.get("evaluated_at", "unknown")
    mode = data.get("mode", "unknown")
    progress = data.get("batch_progress", {})
    status = progress.get("status", "unknown")

    con.print(
        Panel.fit(
            f"Evaluated: [dim]{evaluated_at}[/dim]\n"
            f"Mode: [dim]{mode}[/dim]\n"
            f"Status: [dim]{status}[/dim]",
            title="[bold]Stocktake Results[/bold]",
        )
    )

    skills = normalize_skills(data.get("skills", []))

    # Summary counts
    counts: dict[str, int] = defaultdict(int)
    for skill in skills:
        counts[skill.get("verdict", "Unknown")] += 1

    summary_table = Table(title="[bold]Summary[/bold]", show_header=False, box=ROUNDED)
    summary_table.add_column("Verdict", style="bold", no_wrap=True)
    summary_table.add_column("Count", justify="right", no_wrap=True)

    for verdict in Verdict:
        color = VERDICT_COLORS.get(verdict, "white")
        count = counts.get(verdict.value, 0)
        summary_table.add_row(f"[{color}]{verdict.value}[/{color}]", str(count))

    con.print(summary_table)

    if group_by == "verdict":
        by_verdict: dict[str, list[dict]] = defaultdict(list)
        for skill in skills:
            verdict = skill.get("verdict", "Unknown")
            by_verdict[verdict].append(skill)

        for verdict in Verdict:
            if verdict.value not in by_verdict:
                continue

            items = by_verdict[verdict.value]
            color = VERDICT_COLORS.get(verdict, "white")

            table = Table(
                title=f"[bold {color}]{verdict.value}[/bold {color}] ({len(items)})",
                box=HORIZONTALS,
                show_lines=True,
            )
            table.add_column("Skill", style="cyan", no_wrap=True, width=15)
            table.add_column("7d", justify="right", style="green", no_wrap=True, width=4)
            table.add_column("30d", justify="right", style="yellow", no_wrap=True, width=5)
            table.add_column("Reason", style="dim", width=reason_width)

            for skill in sorted(items, key=lambda x: get_skill_name(x)):
                name = get_skill_name(skill)
                use_7d = skill.get("use_7d", 0)
                use_30d = skill.get("use_30d", 0)
                reason = skill.get("reason", "")
                table.add_row(name, str(use_7d), str(use_30d), reason)

            con.print(table)
    else:
        table = Table(title="[bold]All Skills[/bold]", box=HORIZONTALS, show_lines=True)
        table.add_column("Skill", style="cyan", no_wrap=True, width=15)
        table.add_column("7d", justify="right", style="green", no_wrap=True, width=4)
        table.add_column("30d", justify="right", style="yellow", no_wrap=True, width=5)
        table.add_column("Verdict", style="bold", no_wrap=True, width=9)
        table.add_column("Reason", style="dim", width=reason_width - 9)

        for skill in sorted(skills, key=lambda x: get_skill_name(x)):
            name = get_skill_name(skill)
            use_7d = skill.get("use_7d", 0)
            use_30d = skill.get("use_30d", 0)
            verdict_str = skill.get("verdict", "Unknown")
            reason = skill.get("reason", "")

            # Look up verdict enum for color, fallback to string lookup for non-enum verdicts
            try:
                verdict_enum = Verdict(verdict_str)
                color = VERDICT_COLORS.get(verdict_enum, "white")
            except ValueError:
                color = "white"
            table.add_row(
                name, str(use_7d), str(use_30d), f"[{color}]{verdict_str}[/{color}]", reason
            )

        con.print(table)


# Command: save


def cmd_save(args: argparse.Namespace) -> int:
    """Merge evaluation results into results.json."""
    results_path = args.results or DEFAULT_RESULTS

    # Read eval results from stdin
    try:
        input_json = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error:[/red] Invalid JSON from stdin: {e}")
        return 1

    evaluated_at = datetime.now(local_tz()).strftime("%Y-%m-%dT%H:%M:%S%z")

    # Ensure parent directory exists
    results_path.parent.mkdir(parents=True, exist_ok=True)

    if not results_path.exists():
        # Bootstrap new results file
        input_json["evaluated_at"] = evaluated_at
        # Normalize to array format
        input_json["skills"] = normalize_skills(input_json.get("skills", []))
        with open(results_path, "w") as f:
            json.dump(input_json, f, indent=2)
        console.print(f"[green]Created:[/green] {results_path}")
        return 0

    # Merge with existing
    with open(results_path) as f:
        existing = json.load(f)

    # Merge skills (new overrides old by path)
    if "skills" in input_json:
        new_skills = normalize_skills(input_json["skills"])
        existing_skills = normalize_skills(existing.get("skills", []))

        # Build lookup by path
        by_path = {s.get("path", ""): s for s in existing_skills}
        for skill in new_skills:
            path = skill.get("path", "")
            if path:
                by_path[path] = skill

        existing["skills"] = list(by_path.values())

    # Update metadata
    existing["evaluated_at"] = evaluated_at
    if "mode" in input_json:
        existing["mode"] = input_json["mode"]
    if "batch_progress" in input_json:
        existing["batch_progress"] = input_json["batch_progress"]

    with open(results_path, "w") as f:
        json.dump(existing, f, indent=2)

    console.print(f"[green]Updated:[/green] {results_path}")
    return 0


# Command: merge-chunks


def cmd_merge_chunks(args: argparse.Namespace) -> int:
    """Merge chunked evaluation results with inventory into results.json."""
    results_path = args.results or DEFAULT_RESULTS
    tmp_dir = DEFAULT_TMP_DIR
    inventory_path = args.inventory

    if not tmp_dir.exists():
        console.print(f"[red]Error:[/red] Temp directory not found: {tmp_dir}")
        return 1

    # Load inventory if provided (for use_7d, use_30d, mtime, name)
    # Build lookup by path for merging
    inventory_by_path: dict[str, dict] = {}
    if inventory_path:
        try:
            with open(inventory_path) as f:
                inv_data = json.load(f)
            for skill in inv_data.get("skills", []):
                path = skill.get("path", "")
                if not path:
                    continue
                inventory_by_path[path] = {
                    "name": skill.get("name", ""),
                    "use_7d": skill.get("use_7d", 0),
                    "use_30d": skill.get("use_30d", 0),
                    "mtime": skill.get("mtime", ""),
                }
        except (OSError, json.JSONDecodeError) as e:
            console.print(f"[yellow]Warning:[/yellow] Could not load inventory: {e}")

    # Find all chunk files
    chunk_files = sorted(tmp_dir.glob("chunk_*.json"))
    if not chunk_files:
        console.print(f"[yellow]No chunk files found in[/yellow] {tmp_dir}")
        return 0

    # Load all chunks - expect array format
    all_skills: list[dict] = []
    total_evaluated = 0
    seen_paths: set[str] = set()

    for chunk_file in chunk_files:
        try:
            with open(chunk_file) as f:
                chunk_data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            console.print(f"[yellow]Warning:[/yellow] Skipping {chunk_file}: {e}")
            continue

        # Handle formats: direct array, or object with "skills" key
        if isinstance(chunk_data, list):
            skills_list = chunk_data
        elif isinstance(chunk_data, dict):
            skills_list = normalize_skills(chunk_data.get("skills", []))
        else:
            console.print(f"[yellow]Warning:[/yellow] Unexpected format in {chunk_file}")
            continue

        for eval_item in skills_list:
            path = eval_item.get("path", "")
            if not path or path in seen_paths:
                continue
            seen_paths.add(path)

            # Merge inventory data with evaluation data
            merged = {
                "path": path,
                "verdict": eval_item.get("verdict", "Unknown"),
                "reason": eval_item.get("reason", ""),
            }
            # Add inventory fields if available
            if path in inventory_by_path:
                inv = inventory_by_path[path]
                merged["name"] = inv.get("name", "")
                merged["use_7d"] = inv.get("use_7d", 0)
                merged["use_30d"] = inv.get("use_30d", 0)
                merged["mtime"] = inv.get("mtime", "")
            all_skills.append(merged)
        total_evaluated += len(skills_list)

    if not all_skills:
        console.print("[red]Error:[/red] No skills found in chunk files")
        return 1

    # Build results
    evaluated_at = datetime.now(local_tz()).strftime("%Y-%m-%dT%H:%M:%S%z")

    results = {
        "evaluated_at": evaluated_at,
        "mode": "full",
        "batch_progress": {
            "total": len(all_skills),
            "evaluated": total_evaluated,
            "status": "completed",
        },
        "skills": all_skills,
    }

    # Write results
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)

    console.print(f"[green]Merged[/green] {len(chunk_files)} chunks → {results_path}")
    console.print(f"  Total skills: {len(all_skills)}")

    # Clean up temp files if requested
    if args.clean:
        import shutil

        shutil.rmtree(tmp_dir)
        console.print(f"[dim]Cleaned up[/dim] {tmp_dir}")

    return 0


# Main CLI


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="skill-stocktake CLI — unified inventory and summary tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # scan command
    scan_parser = subparsers.add_parser("scan", help="Phase 1: Inventory all skills")
    scan_parser.add_argument("--global-dir", type=Path, help="Override global skills dir")
    scan_parser.add_argument("--project-dir", type=Path, help="Override project skills dir")
    scan_parser.add_argument(
        "--observations-dir", type=Path, help="Override observations directory"
    )
    scan_parser.add_argument("--output", choices=["json", "rich", "markdown"], default="rich")
    scan_parser.add_argument("--width", type=int, help="Override terminal width for rich output")

    # diff command
    diff_parser = subparsers.add_parser("diff", help="Quick Scan: Find changed skills")
    diff_parser.add_argument("--results", type=Path, help="Path to results.json")
    diff_parser.add_argument("--global-dir", type=Path, help="Override global skills directory")
    diff_parser.add_argument("--project-dir", type=Path, help="Override project skills directory")
    diff_parser.add_argument("--output", choices=["json", "rich"], default="rich")

    # overview command
    overview_parser = subparsers.add_parser("overview", help="Quick overview with usage stats")
    overview_parser.add_argument("--global-dir", type=Path, help="Override global skills dir")
    overview_parser.add_argument("--project-dir", type=Path, help="Override project skills dir")
    overview_parser.add_argument(
        "--observations-dir", type=Path, help="Override observations directory"
    )
    overview_parser.add_argument(
        "--width", type=int, help="Override terminal width for rich output"
    )

    # summary command
    summary_parser = subparsers.add_parser("summary", help="Phase 3: Display results table")
    summary_parser.add_argument("--results", type=Path, help="Path to results.json")
    summary_parser.add_argument("--output", choices=["json", "rich", "markdown"], default="rich")
    summary_parser.add_argument("--group-by", choices=["verdict", "skill"], default="verdict")
    summary_parser.add_argument("--width", type=int, help="Override terminal width for rich output")

    # save command
    save_parser = subparsers.add_parser("save", help="Merge evaluation results")
    save_parser.add_argument("--results", type=Path, help="Path to results.json")

    # merge-chunks command
    merge_parser = subparsers.add_parser("merge-chunks", help="Merge chunked evaluation results")
    merge_parser.add_argument("--results", type=Path, help="Path to results.json")
    merge_parser.add_argument("--inventory", type=Path, help="Path to inventory JSON from scan")
    merge_parser.add_argument("--clean", action="store_true", help="Remove temp files after merge")

    args = parser.parse_args(argv)

    if args.command == "scan":
        return cmd_scan(args)
    elif args.command == "diff":
        return cmd_diff(args)
    elif args.command == "overview":
        return cmd_overview(args)
    elif args.command == "summary":
        return cmd_summary(args)
    elif args.command == "save":
        return cmd_save(args)
    elif args.command == "merge-chunks":
        return cmd_merge_chunks(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
