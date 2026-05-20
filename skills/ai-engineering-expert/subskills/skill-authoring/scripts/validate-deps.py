#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Validate and query metadata.depends-on references across all skills.

Parses every SKILL.md frontmatter, collects metadata.depends-on entries,
and verifies each referenced skill exists in the local skills/ directory,
commands/ directory (early-version skills), or skills-lock.json.

Usage:
    uv run $SKILL_DIR/scripts/validate-deps.py [--fix] [--project-root DIR]
    uv run $SKILL_DIR/scripts/validate-deps.py callers <skill-name> [--project-root DIR]

Modes:
    Default: Report stale references and missing skills.
    callers: List skills that declare metadata.depends-on for the target skill.
    --fix:   Interactively prompt to update stale references after a rename.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml


def find_all_skills(project_root: Path) -> dict[str, Path]:
    """Return {skill_name: path} for all discoverable skills and commands."""
    skills: dict[str, Path] = {}

    # Discover skills from skills/ directory
    skills_dir = project_root / "skills"
    if skills_dir.is_dir():
        for skill_md in skills_dir.rglob("SKILL.md"):
            try:
                content = skill_md.read_text(encoding="utf-8")
                fm = parse_frontmatter(content)
                if fm:
                    name = fm.get("name")
                    if isinstance(name, str):
                        skills[name] = skill_md
            except Exception:
                continue

    # Discover commands from commands/ directory (early-version skills)
    # Command name is derived from filename stem: commands/architect.md -> "architect"
    commands_dir = project_root / "commands"
    if commands_dir.is_dir():
        for cmd_file in commands_dir.glob("*.md"):
            name = cmd_file.stem
            if name:
                skills[name] = cmd_file

    return skills


def find_locked_skills(project_root: Path) -> set[str]:
    """Return skill names from skills-lock.json."""
    lock_path = project_root / "skills-lock.json"
    if not lock_path.is_file():
        return set()
    try:
        data = json.loads(lock_path.read_text(encoding="utf-8"))
        return set(data.get("skills", {}).keys())
    except (json.JSONDecodeError, KeyError):
        return set()


def parse_frontmatter(content: str) -> dict[str, object] | None:
    """Parse YAML frontmatter from markdown content.

    Falls back to targeted extraction for fields we need when full YAML parsing
    fails, such as unquoted descriptions containing colons.
    """
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None
    fm_text = match.group(1)
    try:
        parsed = yaml.safe_load(fm_text)
    except yaml.YAMLError:
        return _parse_frontmatter_fallback(fm_text)
    return parsed if isinstance(parsed, dict) else None


def _parse_frontmatter_fallback(fm_text: str) -> dict[str, object] | None:
    """Extract minimal frontmatter fields needed for dependency validation."""
    result: dict[str, object] = {}
    name_match = re.search(r"^name:\s*(.+)$", fm_text, re.MULTILINE)
    if name_match:
        result["name"] = name_match.group(1).strip().strip('"').strip("'")

    depends_match = re.search(r"depends-on:\s*\[(.+?)\]", fm_text, re.DOTALL)
    if depends_match:
        result["metadata"] = {
            "depends-on": [
                item.strip().strip('"').strip("'")
                for item in depends_match.group(1).split(",")
            ]
        }
    else:
        multiline_match = re.search(r"depends-on:\s*\n((?:\s+-\s+.+\n?)+)", fm_text)
        if multiline_match:
            result["metadata"] = {
                "depends-on": [
                    item.strip().strip('"').strip("'")
                    for item in re.findall(r"-\s+(.+)", multiline_match.group(1))
                ]
            }

    return result if result else None


def _normalize_depends_on(depends_on: object) -> list[str]:
    """Return a normalized list of dependency names from frontmatter data."""
    if isinstance(depends_on, str):
        return [depends_on]
    if isinstance(depends_on, list):
        return [item for item in depends_on if isinstance(item, str)]
    return []


def collect_depends_on(project_root: Path) -> dict[str, list[str]]:
    """Return {skill_name: [depends_on_list]} for all skills with depends-on."""
    deps: dict[str, list[str]] = {}
    skills_dir = project_root / "skills"
    if not skills_dir.is_dir():
        return deps

    for skill_md in skills_dir.rglob("SKILL.md"):
        try:
            content = skill_md.read_text(encoding="utf-8")
            fm = parse_frontmatter(content)
            if not fm:
                continue
            name = fm.get("name", "")
            metadata = fm.get("metadata", {})
            if not isinstance(name, str) or not isinstance(metadata, dict):
                continue
            depends_on = _normalize_depends_on(metadata.get("depends-on", []))
            if depends_on:
                deps[name] = depends_on
        except Exception:
            continue

    return deps


def find_callers(project_root: Path, target_skill: str) -> dict[str, list[str]]:
    """Return skills whose metadata.depends-on includes target_skill."""
    depends_on_map = collect_depends_on(project_root)
    return {
        skill_name: deps
        for skill_name, deps in sorted(depends_on_map.items())
        if target_skill in deps
    }


def validate(project_root: Path) -> list[dict]:
    """Validate all depends-on references. Return list of issues."""
    local_skills = find_all_skills(project_root)
    locked_skills = find_locked_skills(project_root)
    all_available = set(local_skills.keys()) | locked_skills

    depends_on_map = collect_depends_on(project_root)
    issues: list[dict] = []

    for skill_name, deps in depends_on_map.items():
        for dep in deps:
            if dep not in all_available:
                issues.append(
                    {
                        "type": "missing",
                        "skill": skill_name,
                        "depends_on": dep,
                        "message": (
                            f"Skill '{skill_name}' depends on '{dep}', but '{dep}' not found "
                            "in skills/, commands/, or skills-lock.json"
                        ),
                    }
                )

    return issues


def find_rename_candidates(project_root: Path, old_name: str) -> list[str]:
    """Find potential rename targets by fuzzy matching skill names."""
    local_skills = find_all_skills(project_root)
    locked_skills = find_locked_skills(project_root)
    all_names = sorted(set(local_skills.keys()) | locked_skills)

    # Simple prefix/substring matching
    candidates = []
    for name in all_names:
        if old_name in name or name in old_name:
            candidates.append(name)
        elif old_name.replace("-", "") in name.replace("-", ""):
            candidates.append(name)

    return candidates


def fix_stale_references(project_root: Path, issues: list[dict]) -> None:
    """Interactively fix stale depends-on references."""
    local_skills = find_all_skills(project_root)

    for issue in issues:
        if issue["type"] != "missing":
            continue

        old_name = issue["depends_on"]
        skill_name = issue["skill"]
        skill_path = local_skills.get(skill_name)

        if not skill_path:
            print(f"  Cannot find SKILL.md for '{skill_name}', skipping.")
            continue

        candidates = find_rename_candidates(project_root, old_name)

        print(f"\n  Stale reference: '{skill_name}' depends-on '{old_name}' (not found)")
        if candidates:
            print("  Possible rename targets:")
            for i, c in enumerate(candidates, 1):
                print(f"    {i}. {c}")
            print(f"    0. Skip (keep '{old_name}')")
            print("    s. Enter custom name")

            choice = input("  Choose: ").strip()
            if choice == "0" or choice == "":
                continue
            elif choice == "s":
                new_name = input("  New skill name: ").strip()
                if not new_name:
                    continue
            elif choice.isdigit() and 1 <= int(choice) <= len(candidates):
                new_name = candidates[int(choice) - 1]
            else:
                print("  Invalid choice, skipping.")
                continue
        else:
            new_name = input("  Enter correct skill name (or Enter to skip): ").strip()
            if not new_name:
                continue

        # Update the SKILL.md file
        content = skill_path.read_text(encoding="utf-8")
        fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if not fm_match:
            print(f"  Cannot parse frontmatter in {skill_path}, skipping.")
            continue

        fm_text = fm_match.group(1)
        # Replace in the depends-on list
        # Handle both list format and string format
        new_fm = fm_text.replace(f"- {old_name}", f"- {new_name}")
        new_fm = new_fm.replace(f"[{old_name}]", f"[{new_name}]")

        if new_fm != fm_text:
            new_content = content[: fm_match.start(1)] + new_fm + content[fm_match.end(1) :]
            skill_path.write_text(new_content, encoding="utf-8")
            print(
                f"  Updated: '{old_name}' -> '{new_name}' in {skill_path.relative_to(project_root)}"
            )
        else:
            print(f"  Could not find '{old_name}' in frontmatter to replace. Manual edit needed.")


def _validate_project_root(root: Path) -> bool:
    """Return True when root looks like a skills project."""
    if not (root / "skills").is_dir():
        print(f"Error: No skills/ directory found in {root}", file=sys.stderr)
        return False
    return True


def print_callers(project_root: Path, target_skill: str) -> int:
    """Print inbound depends-on callers for target_skill."""
    callers = find_callers(project_root, target_skill)
    if not callers:
        print(f"No skills declare metadata.depends-on for '{target_skill}'.")
        return 0

    local_skills = find_all_skills(project_root)
    print(f"Skills declaring metadata.depends-on for '{target_skill}':")
    for skill_name in callers:
        skill_path = local_skills.get(skill_name)
        if skill_path:
            display_path = skill_path.relative_to(project_root)
            print(f"  - {skill_name}: {display_path}")
        else:
            print(f"  - {skill_name}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate and query metadata.depends-on references"
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=["callers"],
        help="Query mode: callers lists skills that depend on the target skill",
    )
    parser.add_argument(
        "skill_name",
        nargs="?",
        help="Target skill name for query modes",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Interactively fix stale references after a rename",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory (default: cwd)",
    )
    args = parser.parse_args()

    root = args.project_root.resolve()
    if not _validate_project_root(root):
        return 1

    if args.command == "callers":
        if args.fix:
            print("Error: --fix cannot be used with callers mode", file=sys.stderr)
            return 2
        if not args.skill_name:
            print("Error: callers mode requires <skill-name>", file=sys.stderr)
            return 2
        return print_callers(root, args.skill_name)

    if args.skill_name:
        print("Error: <skill-name> is only valid with callers mode", file=sys.stderr)
        return 2

    issues = validate(root)

    if not issues:
        print("All depends-on references are valid.")
        return 0

    print(f"Found {len(issues)} issue(s):\n")
    for issue in issues:
        print(f"  [{issue['type'].upper()}] {issue['message']}")

    if args.fix:
        print("\n--- Fix Mode ---")
        fix_stale_references(root, issues)

        # Re-validate
        remaining = validate(root)
        if remaining:
            print(f"\n{len(remaining)} issue(s) remaining after fixes.")
            return 1
        else:
            print("\nAll issues resolved.")
            return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
