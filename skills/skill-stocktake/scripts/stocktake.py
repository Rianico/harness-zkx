#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["rich>=13.0.0"]
# ///
"""skill-stocktake CLI — unified inventory and summary tool.

Usage:
    uv run stocktake.py scan [--output json|rich|markdown]
    uv run stocktake.py diff [--results PATH]
    uv run stocktake.py summary [--results PATH] [--output rich|markdown|json]
    uv run stocktake.py save [--results PATH] < eval.json

Commands:
    scan     Phase 1: Inventory all skills
    diff     Quick Scan: Find changed skills since last run
    summary  Phase 3: Display results table
    save     Merge evaluation results into results.json
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

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Defaults
DEFAULT_GLOBAL_DIR = Path.home() / ".claude" / "skills"
DEFAULT_OBSERVATIONS_DIR = Path.home() / ".claude" / "lsz" / "homunculus"
DEFAULT_RESULTS = Path.home() / ".claude" / "skills" / "skill-stocktake" / "results.json"


console = Console()


# Verdict enum for type-safe verdict strings
class Verdict(StrEnum):
    """Verdict categories for skill evaluations."""
    KEEP = "Keep"
    IMPROVE = "Improve"
    UPDATE = "Update"
    MERGE = "Merge"
    RETIRE = "Retire"


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
) -> tuple[dict[str, int], dict[str, int]]:
    """Count Read tool observations per file path in single pass.

    Returns tuple of (counts_7d, counts_30d) for use in scan operations.
    """
    now = datetime.now(UTC)
    cutoff_7d = now - timedelta(days=7)
    cutoff_30d = now - timedelta(days=30)
    cutoff_7d_str = cutoff_7d.strftime("%Y-%m-%dT%H:%M:%SZ")
    cutoff_30d_str = cutoff_30d.strftime("%Y-%m-%dT%H:%M:%SZ")

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

                    # Single pass: check both windows
                    if timestamp >= cutoff_7d_str:
                        counts_7d[file_path] = counts_7d.get(file_path, 0) + 1
                    if timestamp >= cutoff_30d_str:
                        counts_30d[file_path] = counts_30d.get(file_path, 0) + 1
        except OSError:
            continue

    return counts_7d, counts_30d


def _format_path_with_tilde(path: Path | str) -> str:
    """Format path with tilde prefix if under home directory."""
    path_obj = Path(path) if isinstance(path, str) else path
    home = Path.home()
    path_str = str(path_obj)
    home_str = str(home)
    if path_str.startswith(home_str):
        return "~" + path_str[len(home_str):]
    return path_str


def _walk_skills_dir(
    skills_dir: Path, followlinks: bool = True
) -> Generator[Path, None, None]:
    """Walk skills directory and yield all .md files."""
    for root, _, files in os.walk(skills_dir, followlinks=followlinks):
        root_path = Path(root)
        for filename in files:
            if filename.endswith(".md"):
                yield root_path / filename


def scan_skills_dir(
    skills_dir: Path,
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

        resolved_path = str(md_file.resolve()) if md_file.is_symlink() else str(md_file)
        file_path_7d = use_7d.get(resolved_path, use_7d.get(str(md_file), 0))
        file_path_30d = use_30d.get(resolved_path, use_30d.get(str(md_file), 0))

        skills.append({
            "path": path_str,
            "name": frontmatter.get("name", ""),
            "description": frontmatter.get("description", ""),
            "use_7d": file_path_7d,
            "use_30d": file_path_30d,
            "mtime": get_mtime_utc(md_file),
        })

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

    # Get observation counts (single pass returns both windows)
    obs_files = get_observation_files(observations_dir)
    use_7d, use_30d = count_read_observations(obs_files)

    # Scan directories
    global_skills = scan_skills_dir(global_dir, use_7d, use_30d)
    project_skills = scan_skills_dir(project_dir, use_7d, use_30d) if project_dir.exists() else []

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
        render_scan_rich(data)

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
        name = skill["name"] or Path(skill["path"]).stem
        desc = skill["description"]
        if len(desc) > 60:
            desc = desc[:60] + "..."
        desc = desc.replace("|", "\\|")
        lines.append(f"| {name} | {skill['use_7d']} | {skill['use_30d']} | {desc} |")

    return "\n".join(lines)


def render_scan_rich(data: dict) -> None:
    """Render scan results with rich tables."""
    summary = data["scan_summary"]

    # Scan summary panel
    project_status = "green" if summary["project"]["found"] else "red"
    project_check = "✓" if summary["project"]["found"] else "✗"
    console.print(Panel.fit(
        f"[green]✓[/green] ~/.claude/skills/ ({summary['global']['count']} files)\n"
        f"[{project_status}]{project_check}[/] "
        f"{summary['project']['path'] or 'project skills'} ({summary['project']['count']} files)",
        title="[bold]Scanning[/bold]",
    ))

    # Skills table
    table = Table(title=f"[bold]Inventory[/bold] ({len(data['skills'])} skills)")
    table.add_column("Skill", style="cyan")
    table.add_column("7d", justify="right", style="green")
    table.add_column("30d", justify="right", style="yellow")
    table.add_column("Description", style="dim")

    for skill in data["skills"]:
        name = skill["name"] or Path(skill["path"]).stem
        desc = skill["description"]
        if len(desc) > 50:
            desc = desc[:50] + "..."
        table.add_row(name, str(skill["use_7d"]), str(skill["use_30d"]), desc)

    console.print(table)


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

    known_paths = set(results.get("skills", {}).keys())
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
            changed.append({
                "path": path_str,
                "name": skill_name,
                "mtime": mtime,
                "is_new": is_new,
            })

    return changed


def render_diff_rich(changed: list[dict], evaluated_at: str) -> None:
    """Render diff results with rich."""
    if not changed:
        console.print(Panel.fit(
            f"No changes since [dim]{evaluated_at}[/dim]",
            title="[bold]Quick Scan[/bold]",
            style="green",
        ))
        return

    console.print(Panel.fit(
        f"Last evaluated: [dim]{evaluated_at}[/dim]",
        title="[bold]Quick Scan[/bold]",
    ))

    table = Table(title=f"[bold]Changed Skills[/bold] ({len(changed)})")
    table.add_column("Skill", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Modified", style="dim")

    for item in sorted(changed, key=lambda x: x["name"]):
        status = "[green]NEW[/green]" if item["is_new"] else "[yellow]MODIFIED[/yellow]"
        table.add_row(item["name"], status, item["mtime"])

    console.print(table)


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
        render_summary_rich(data, args.group_by)

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

    skills = data.get("skills", {})

    if group_by == "verdict":
        by_verdict: dict[str, list[tuple[str, dict]]] = defaultdict(list)
        for name, info in skills.items():
            verdict = info.get("verdict", "Unknown")
            by_verdict[verdict].append((name, info))

        for verdict in Verdict:
            if verdict.value not in by_verdict:
                continue

            items = by_verdict[verdict]
            lines.append(f"### {verdict} ({len(items)})")
            lines.append("")
            lines.append("| Skill | 7d | Reason |")
            lines.append("|-------|-----|--------|")

            for name, info in sorted(items, key=lambda x: x[0]):
                use_7d = info.get("use_7d", 0)
                reason = info.get("reason", "")
                if len(reason) > 80:
                    reason = reason[:77] + "..."
                reason = reason.replace("|", "\\|")
                lines.append(f"| {name} | {use_7d} | {reason} |")

            lines.append("")
    else:
        lines.append("| Skill | 7d | Verdict | Reason |")
        lines.append("|-------|-----|---------|--------|")

        for name in sorted(skills.keys()):
            info = skills[name]
            use_7d = info.get("use_7d", 0)
            verdict = info.get("verdict", "Unknown")
            reason = info.get("reason", "")
            if len(reason) > 60:
                reason = reason[:57] + "..."
            reason = reason.replace("|", "\\|")
            lines.append(f"| {name} | {use_7d} | {verdict} | {reason} |")

    # Summary counts
    lines.append("### Summary")
    lines.append("")
    lines.append("| Verdict | Count |")
    lines.append("|---------|-------|")

    counts: dict[str, int] = defaultdict(int)
    for info in skills.values():
        counts[info.get("verdict", "Unknown")] += 1

    for verdict in Verdict:
        lines.append(f"| {verdict.value} | {counts.get(verdict.value, 0)} |")

    return "\n".join(lines)


def format_summary_json(data: dict) -> str:
    """Format results as compact JSON."""
    skills = data.get("skills", {})

    summary = {
        "evaluated_at": data.get("evaluated_at"),
        "mode": data.get("mode"),
        "total": len(skills),
        "by_verdict": defaultdict(list),
        "skills": [],
    }

    for name, info in sorted(skills.items()):
        summary["skills"].append({
            "name": name,
            "verdict": info.get("verdict"),
            "use_7d": info.get("use_7d", 0),
            "reason": info.get("reason", "")[:100],
        })
        summary["by_verdict"][info.get("verdict", "Unknown")].append(name)

    summary["by_verdict"] = dict(summary["by_verdict"])
    return json.dumps(summary, indent=2)


def render_summary_rich(data: dict, group_by: str) -> None:
    """Render results with rich tables."""
    evaluated_at = data.get("evaluated_at", "unknown")
    mode = data.get("mode", "unknown")
    progress = data.get("batch_progress", {})
    status = progress.get("status", "unknown")

    console.print(Panel.fit(
        f"Evaluated: [dim]{evaluated_at}[/dim]\n"
        f"Mode: [dim]{mode}[/dim]\n"
        f"Status: [dim]{status}[/dim]",
        title="[bold]Stocktake Results[/bold]",
    ))

    skills = data.get("skills", {})

    # Summary counts
    counts: dict[str, int] = defaultdict(int)
    for info in skills.values():
        counts[info.get("verdict", "Unknown")] += 1

    summary_table = Table(title="[bold]Summary[/bold]", show_header=False)
    summary_table.add_column("Verdict", style="bold")
    summary_table.add_column("Count", justify="right")

    verdict_colors = {
        Verdict.KEEP: "green",
        Verdict.IMPROVE: "yellow",
        Verdict.UPDATE: "blue",
        Verdict.MERGE: "magenta",
        Verdict.RETIRE: "red",
    }

    for verdict in Verdict:
        color = verdict_colors.get(verdict, "white")
        count = counts.get(verdict.value, 0)
        summary_table.add_row(f"[{color}]{verdict.value}[/{color}]", str(count))

    console.print(summary_table)

    if group_by == "verdict":
        by_verdict: dict[str, list[tuple[str, dict]]] = defaultdict(list)
        for name, info in skills.items():
            verdict = info.get("verdict", "Unknown")
            by_verdict[verdict].append((name, info))

        for verdict in Verdict:
            if verdict.value not in by_verdict:
                continue

            items = by_verdict[verdict.value]
            color = verdict_colors.get(verdict, "white")

            table = Table(title=f"[bold {color}]{verdict.value}[/bold {color}] ({len(items)})")
            table.add_column("Skill", style="cyan")
            table.add_column("7d", justify="right", style="green")
            table.add_column("Reason", style="dim")

            for name, info in sorted(items, key=lambda x: x[0]):
                use_7d = info.get("use_7d", 0)
                reason = info.get("reason", "")
                if len(reason) > 60:
                    reason = reason[:57] + "..."
                table.add_row(name, str(use_7d), reason)

            console.print(table)
    else:
        table = Table(title="[bold]All Skills[/bold]")
        table.add_column("Skill", style="cyan")
        table.add_column("7d", justify="right")
        table.add_column("Verdict", style="bold")
        table.add_column("Reason", style="dim")

        for name in sorted(skills.keys()):
            info = skills[name]
            use_7d = info.get("use_7d", 0)
            verdict_str = info.get("verdict", "Unknown")
            reason = info.get("reason", "")
            if len(reason) > 50:
                reason = reason[:47] + "..."

            # Look up verdict enum for color, fallback to string lookup for non-enum verdicts
            try:
                verdict_enum = Verdict(verdict_str)
                color = verdict_colors.get(verdict_enum, "white")
            except ValueError:
                color = "white"
            table.add_row(name, str(use_7d), f"[{color}]{verdict_str}[/{color}]", reason)

        console.print(table)


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

    evaluated_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Ensure parent directory exists
    results_path.parent.mkdir(parents=True, exist_ok=True)

    if not results_path.exists():
        # Bootstrap new results file
        input_json["evaluated_at"] = evaluated_at
        with open(results_path, "w") as f:
            json.dump(input_json, f, indent=2)
        console.print(f"[green]Created:[/green] {results_path}")
        return 0

    # Merge with existing
    with open(results_path) as f:
        existing = json.load(f)

    # Merge skills (new overrides old)
    if "skills" in input_json:
        existing["skills"] = {**existing.get("skills", {}), **input_json["skills"]}

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

    # diff command
    diff_parser = subparsers.add_parser("diff", help="Quick Scan: Find changed skills")
    diff_parser.add_argument("--results", type=Path, help="Path to results.json")
    diff_parser.add_argument("--global-dir", type=Path, help="Override global skills directory")
    diff_parser.add_argument("--project-dir", type=Path, help="Override project skills directory")
    diff_parser.add_argument("--output", choices=["json", "rich"], default="rich")

    # summary command
    summary_parser = subparsers.add_parser("summary", help="Phase 3: Display results table")
    summary_parser.add_argument("--results", type=Path, help="Path to results.json")
    summary_parser.add_argument("--output", choices=["json", "rich", "markdown"], default="rich")
    summary_parser.add_argument("--group-by", choices=["verdict", "skill"], default="verdict")

    # save command
    save_parser = subparsers.add_parser("save", help="Merge evaluation results")
    save_parser.add_argument("--results", type=Path, help="Path to results.json")

    args = parser.parse_args(argv)

    if args.command == "scan":
        return cmd_scan(args)
    elif args.command == "diff":
        return cmd_diff(args)
    elif args.command == "summary":
        return cmd_summary(args)
    elif args.command == "save":
        return cmd_save(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
