#!/usr/bin/env python3
"""Phase 1 inventory scan for skill-stocktake.

Enumerates skill files, extracts frontmatter, aggregates observations,
and outputs structured JSON for Phase 2 evaluation.

Usage:
    python scan.py [OPTIONS]

Options:
    --global-dir PATH    Override global skills directory
    --project-dir PATH   Override project skills directory
    --observations-dir PATH  Override observations directory
    --output FORMAT      Output format: json (default) or markdown
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Defaults
DEFAULT_GLOBAL_DIR = Path.home() / ".claude" / "skills"
DEFAULT_OBSERVATIONS_DIR = Path.home() / ".claude" / "lsz" / "homunculus"


def extract_frontmatter(content: str) -> dict[str, str]:
    """Extract YAML frontmatter from markdown content.

    Handles both quoted and unquoted single-line values.
    Does NOT support multi-line YAML blocks.
    """
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
            # Remove surrounding quotes
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            result[key] = value

    return result


def get_mtime_utc(path: Path) -> str:
    """Get file modification time as ISO 8601 UTC string."""
    mtime = path.stat().st_mtime
    dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def get_observation_files(observations_dir: Path) -> list[Path]:
    """Get all observation files (global + project-specific)."""
    files = []

    # Global observations
    global_file = observations_dir / "observations.jsonl"
    if global_file.exists():
        files.append(global_file)

    # Project-specific observations
    projects_dir = observations_dir / "projects"
    if projects_dir.exists():
        for project_dir in projects_dir.iterdir():
            if project_dir.is_dir():
                obs_file = project_dir / "observations.jsonl"
                if obs_file.exists():
                    files.append(obs_file)

    return files


def count_read_observations(observations_files: list[Path], days: int) -> dict[str, int]:
    """Count Read tool observations per file path in the last N days.

    Returns dict mapping file_path -> count.
    """
    from datetime import timedelta

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")

    counts: dict[str, int] = {}

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

                    # Filter: Read tool, within time window
                    if obs.get("tool") != "Read":
                        continue

                    timestamp = obs.get("timestamp", "")
                    if timestamp < cutoff_str:
                        continue

                    # Get file path from input.file_path
                    file_path = obs.get("input", {}).get("file_path")
                    if file_path:
                        counts[file_path] = counts.get(file_path, 0) + 1
        except OSError:
            continue

    return counts


def scan_skills_dir(
    skills_dir: Path,
    use_7d: dict[str, int],
    use_30d: dict[str, int],
    follow_symlinks: bool = True,
) -> list[dict]:
    """Scan a skills directory and return list of skill metadata.

    Args:
        skills_dir: Directory to scan for .md files
        use_7d: Dict of file path -> 7-day usage count
        use_30d: Dict of file path -> 30-day usage count
        follow_symlinks: Whether to follow symlinked directories

    Returns:
        List of skill metadata dicts sorted by path
    """
    import os

    skills = []

    if not skills_dir.exists():
        return skills

    # Walk the directory tree, optionally following symlinks
    for root, _, files in os.walk(skills_dir, followlinks=follow_symlinks):
        root_path = Path(root)

        for filename in files:
            if not filename.endswith(".md"):
                continue

            md_file = root_path / filename

            try:
                content = md_file.read_text()
            except OSError:
                continue

            frontmatter = extract_frontmatter(content)

            # Normalize path with ~ for home
            path_str = str(md_file)
            home_str = str(Path.home())
            if path_str.startswith(home_str):
                path_str = "~" + path_str[len(home_str):]

            # Get usage counts - try both resolved and original path
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

    # Sort by path
    skills.sort(key=lambda s: s["path"])
    return skills


def run_scan(
    global_dir: Path,
    project_dir: Path | None,
    observations_dir: Path,
) -> dict:
    """Run the full inventory scan."""
    # Get observation files and counts
    obs_files = get_observation_files(observations_dir)
    use_7d = count_read_observations(obs_files, 7)
    use_30d = count_read_observations(obs_files, 30)

    # Scan global skills
    global_skills = scan_skills_dir(global_dir, use_7d, use_30d)

    # Scan project skills
    project_skills = []
    project_path = ""
    if project_dir and project_dir.exists():
        project_skills = scan_skills_dir(project_dir, use_7d, use_30d)
        project_path = str(project_dir)

    # Combine all skills
    all_skills = global_skills + project_skills

    return {
        "scan_summary": {
            "global": {
                "found": global_dir.exists(),
                "count": len(global_skills),
            },
            "project": {
                "found": project_dir is not None and project_dir.exists(),
                "path": project_path,
                "count": len(project_skills),
            },
        },
        "skills": all_skills,
    }


def format_markdown_summary(data: dict) -> str:
    """Format scan summary as markdown table."""
    lines = []

    # Scan summary
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

    # Skills table
    lines.append("| Skill | 7d | 30d | Description |")
    lines.append("|-------|-----|------|-------------|")

    for skill in data["skills"]:
        name = skill["name"] or Path(skill["path"]).stem
        desc = skill["description"][:60] + "..." if len(skill["description"]) > 60 else skill["description"]
        desc = desc.replace("|", "\\|")  # Escape pipes
        lines.append(f"| {name} | {skill['use_7d']} | {skill['use_30d']} | {desc} |")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 1 inventory scan")
    parser.add_argument("--global-dir", type=Path, default=DEFAULT_GLOBAL_DIR)
    parser.add_argument("--project-dir", type=Path, default=None)
    parser.add_argument("--observations-dir", type=Path, default=DEFAULT_OBSERVATIONS_DIR)
    parser.add_argument("--output", choices=["json", "markdown"], default="json")
    parser.add_argument("--project-cwd", type=Path, default=None,
                        help="Auto-detect project dir from CWD/.claude/skills")

    args = parser.parse_args(argv)

    # Determine project directory
    project_dir = args.project_dir
    if project_dir is None and args.project_cwd:
        project_dir = args.project_cwd / ".claude" / "skills"
    elif project_dir is None:
        # Auto-detect from CWD
        project_dir = Path.cwd() / ".claude" / "skills"

    # Run scan
    data = run_scan(args.global_dir, project_dir, args.observations_dir)

    # Output
    if args.output == "json":
        print(json.dumps(data, indent=2))
    else:
        print(format_markdown_summary(data))

    return 0


if __name__ == "__main__":
    sys.exit(main())
