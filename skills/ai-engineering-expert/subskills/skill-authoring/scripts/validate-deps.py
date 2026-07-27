#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-frontmatter>=1.0.0", "pyyaml>=6.0", "rich>=13.0.0"]
# ///
"""
LSZ Skill Management Tool (validate-deps.py)
A versatile script for validating, linting, and fixing LSZ skill metadata.

Supports:
- check: Validate all skill dependencies (depends-on)
- related: Show inbound and outbound dependencies for a skill
- lint: Check skill frontmatter for quality and conventions
- fix: Automatically fix common frontmatter issues (like block scalars)
- rename: Rename a skill and cascade updates to all references
- sync: Generate agents/openai.yaml from SKILL.md canonical metadata
- context-check: Enforce context-load policy (hard gates + soft warnings)
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import frontmatter  # pyright: ignore[reportMissingImports]
    # Reason: resolved by uv run via inline script metadata; not a project dependency
except ImportError:
    print(
        "ERROR: python-frontmatter is required. Install with: uv add python-frontmatter",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    import yaml

    HAS_YAML = True  # pyright: ignore[reportConstantRedefinition]
except ImportError:
    HAS_YAML = False  # pyright: ignore[reportConstantRedefinition]


@dataclass(frozen=True)
class SkillRegistry:
    """Registry of all discoverable skills and their dependency graph."""

    skill_map: dict[str, Path]
    dependency_graph: dict[str, list[str]]


def parse_frontmatter(content: str) -> dict[str, object] | None:
    """Parse YAML frontmatter from markdown content using python-frontmatter."""
    try:
        post = frontmatter.loads(content)
        return post.metadata
    except Exception:
        return None


def _scan_skills_dir(skills_dir: Path) -> tuple[dict[str, Path], dict[str, list[str]]]:
    """Walk skills/ tree and return (skill_map, dependency_graph) from SKILL.md files."""
    skill_map: dict[str, Path] = {}
    dependency_graph: dict[str, list[str]] = {}

    if not skills_dir.exists():
        return skill_map, dependency_graph

    for skill_file in skills_dir.rglob("SKILL.md"):
        try:
            content = skill_file.read_text(encoding="utf-8")
            fm = parse_frontmatter(content)
            if not fm or "name" not in fm:
                continue

            name = str(fm["name"])
            skill_map[name] = skill_file

            metadata = fm.get("metadata", {})
            if not isinstance(metadata, dict):
                continue

            dependencies = metadata.get("depends-on", [])
            if isinstance(dependencies, str):
                dependencies = [dependencies]

            for dep in dependencies:
                if dep not in dependency_graph:
                    dependency_graph[dep] = []
                dependency_graph[dep].append(name)
        except Exception:
            continue

    return skill_map, dependency_graph


def _scan_lock_file(lock_file: Path) -> dict[str, Path]:
    """Add skills from skills-lock.json not already in the map."""
    if not lock_file.exists():
        return {}

    try:
        lock_data = json.loads(lock_file.read_text(encoding="utf-8"))
        return {name: lock_file for name in lock_data.get("skills", {}).keys()}
    except Exception:
        return {}


def _scan_commands_dir(commands_dir: Path) -> dict[str, Path]:
    """Add commands from commands/ directory not already in the map."""
    if not commands_dir.is_dir():
        return {}

    return {cmd_file.stem: cmd_file for cmd_file in commands_dir.glob("*.md") if cmd_file.stem}


def scan_skills(root_dir: Path) -> SkillRegistry:
    """Scan all skill sources and return a SkillRegistry."""
    skills_dir = root_dir / "skills"
    lock_file = root_dir / "skills-lock.json"
    commands_dir = root_dir / "commands"

    skill_map: dict[str, Path] = {}
    dependency_graph: dict[str, list[str]] = {}

    # Phase 1: Scan skills/ directory
    sm, dg = _scan_skills_dir(skills_dir)
    skill_map.update(sm)
    for dep, callers in dg.items():
        if dep not in dependency_graph:
            dependency_graph[dep] = []
        dependency_graph[dep].extend(callers)

    # Phase 2: Add lock file entries not already in map
    for name, path in _scan_lock_file(lock_file).items():
        if name not in skill_map:
            skill_map[name] = path

    # Phase 3: Add command entries not already in map
    for name, path in _scan_commands_dir(commands_dir).items():
        if name not in skill_map:
            skill_map[name] = path

    return SkillRegistry(skill_map=skill_map, dependency_graph=dependency_graph)


def check_all_dependencies(root_dir: Path, skill_map: dict[str, Path]) -> bool:
    print("Validating all 'depends-on' entries...")
    found_errors = False
    for skill_name, location in skill_map.items():
        if location.name == "skills-lock.json":
            continue

        try:
            content = location.read_text(encoding="utf-8")
            fm = parse_frontmatter(content)
            if not fm:
                continue

            metadata = fm.get("metadata", {})
            if not isinstance(metadata, dict):
                continue

            dependencies = metadata.get("depends-on", [])
            if isinstance(dependencies, str):
                dependencies = [dependencies]

            for dep in dependencies:
                if dep not in skill_map:
                    print(
                        f"ERROR: Skill '{skill_name}'"
                        f" ({location.relative_to(root_dir)})"
                        f" depends on missing skill '{dep}'"
                    )
                    found_errors = True
        except Exception as e:
            print(f"Warning: Failed to parse {location} during validation: {e}")

    if not found_errors:
        print("All dependencies validated successfully.")
    return found_errors


def show_related(
    target_skill: str,
    root_dir: Path,
    skill_map: dict[str, Path],
    dependency_graph: dict[str, list[str]],
):
    location = skill_map.get(target_skill)
    if not location:
        print(f"Error: Skill '{target_skill}' not found.")
        return

    print(f"--- Skill: {target_skill} ---")
    print(f"Location: {location.relative_to(root_dir) if isinstance(location, Path) else location}")

    # 1. Outbound Dependencies
    print("\nOutbound Dependencies (depends-on):")
    if location == root_dir / "skills-lock.json":
        print("  (Managed by skills-lock.json, outbound deps not visible)")
    else:
        try:
            content = location.read_text(encoding="utf-8")
            fm = parse_frontmatter(content)
            if not fm:
                print("  (Error parsing frontmatter)")
            else:
                metadata = fm.get("metadata", {})
                dependencies = metadata.get("depends-on", []) if isinstance(metadata, dict) else []
                if isinstance(dependencies, str):
                    dependencies = [dependencies]

                if not dependencies:
                    print("  (None)")
                else:
                    for dep in sorted(dependencies):
                        status = " [OK]" if dep in skill_map else " [MISSING]"
                        print(f"  -> {dep}{status}")
        except Exception as e:
            print(f"  Error: {e}")

    # 2. Inbound Dependencies
    print("\nInbound Dependencies (callers):")
    callers = dependency_graph.get(target_skill, [])
    if not callers:
        print("  (None)")
    else:
        for caller in sorted(callers):
            caller_loc = skill_map.get(caller)
            loc_str = (
                str(caller_loc.relative_to(root_dir)) if isinstance(caller_loc, Path) else "Unknown"
            )
            print(f"  <- {caller} ({loc_str})")


SCALAR_RULES: dict[str, str] = {
    "description": ">-",
    "argument-hint": "|-",
}
"""Required YAML block scalar per frontmatter field."""


def _detect_scalar(fm_text: str, field: str) -> str:
    """Extract the block scalar indicator used by a frontmatter field."""
    m = re.search(rf"^{field}:\s*([|>][-+]?)", fm_text, re.MULTILINE)
    return m.group(1) if m else "inline"


def _check_duplicate_skill_names(root_dir: Path) -> bool:
    """Check that no sub-skill name collides with a top-level skill name."""
    name_paths: dict[str, list[Path]] = {}
    skills_dir = root_dir / "skills"
    if not skills_dir.exists():
        return False

    for skill_file in skills_dir.rglob("SKILL.md"):
        content = skill_file.read_text(encoding="utf-8")
        fm = parse_frontmatter(content)
        if not fm or "name" not in fm:
            continue
        name = str(fm["name"])
        if name not in name_paths:
            name_paths[name] = []
        name_paths[name].append(skill_file)

    found = False
    for name, paths in name_paths.items():
        if len(paths) < 2:
            continue
        rels = [p.relative_to(root_dir) for p in paths]
        print(f"LINT FAIL: Skill name '{name}' is declared by {len(paths)} files:")
        for rel in rels:
            print(f"  - {rel}")
        found = True
    return found


def lint_skills(root_dir: Path, skill_map: dict[str, Path]) -> bool:
    print("Linting skill frontmatter...")
    found_issues = False

    # Structural check: no name collisions
    if _check_duplicate_skill_names(root_dir):
        found_issues = True
    for _, location in skill_map.items():
        if location.name == "skills-lock.json":
            continue

        try:
            content = location.read_text(encoding="utf-8")
            fm = parse_frontmatter(content)
            if not fm:
                print(f"LINT FAIL: {location.relative_to(root_dir)} - Invalid frontmatter")
                found_issues = True
                continue

            # Check required fields
            for field in ["name", "description"]:
                if field not in fm:
                    print(
                        "LINT FAIL:"
                        f" {location.relative_to(root_dir)}"
                        f" - Missing required field '{field}'"
                    )
                    found_issues = True

            # Check per-field block scalar rules
            match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
            if match:
                fm_text = match.group(1)
                for field, expected_scalar in SCALAR_RULES.items():
                    field_present = re.search(rf"^{field}:", fm_text, re.MULTILINE)
                    if not field_present:
                        continue

                    # Check if it uses ANY block scalar
                    uses_block = re.search(rf"^{field}:\s*[|>]", fm_text, re.MULTILINE)
                    if not uses_block:
                        print(
                            "LINT FAIL:"
                            f" {location.relative_to(root_dir)}"
                            f" - '{field}' must be a YAML block scalar"
                            f" ({expected_scalar}), got inline value"
                        )
                        found_issues = True
                        continue

                    # Check if it uses the CORRECT block scalar
                    correct = re.search(
                        rf"^{field}:\s*{re.escape(expected_scalar)}",
                        fm_text,
                        re.MULTILINE,
                    )
                    if not correct:
                        actual = _detect_scalar(fm_text, field)
                        print(
                            "LINT FAIL:"
                            f" {location.relative_to(root_dir)}"
                            f" - '{field}' must use"
                            f" {expected_scalar}, got {actual}"
                        )
                        found_issues = True

        except Exception as e:
            print(f"Error linting {location}: {e}")

    if not found_issues:
        print("Lint passed.")
    return found_issues


def fix_skills(root_dir: Path, skill_map: dict[str, Path], dry_run: bool = False) -> bool:
    """Fix frontmatter issues. Returns True if all OK, False if post-verification fails."""
    msg = (
        "Fixing skill frontmatter..."
        if not dry_run
        else "Checking what would be fixed (dry-run)..."
    )
    print(msg)
    fixed_count = 0
    for _, location in skill_map.items():
        if location.name == "skills-lock.json":
            continue

        try:
            content = location.read_text(encoding="utf-8")
            match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
            if not match:
                continue

            fm_text = match.group(1)
            lines = fm_text.splitlines()
            new_lines: list[str] = []
            changed = False

            for line in lines:
                key = line.split(":", 1)[0].strip()
                if key not in SCALAR_RULES:
                    new_lines.append(line)
                    continue

                expected = SCALAR_RULES[key]

                # Check for inline value (no block scalar indicator)
                field_decl = re.match(rf"^{key}:\s*(.*)", line)
                if not field_decl:
                    new_lines.append(line)
                    continue

                rest = field_decl.group(1).strip()

                # Skip empty values (e.g., "description:" with nothing after)
                if not rest:
                    new_lines.append(line)
                    continue

                # Not a block scalar at all — inline value
                if not re.match(r"[|>]", rest):
                    val = rest
                    if (val.startswith('"') and val.endswith('"')) or (
                        val.startswith("'") and val.endswith("'")
                    ):
                        val = val[1:-1]
                    val = val.replace('\\"', '"').replace("\\'", "'")

                    new_lines.append(f"{key}: {expected}")
                    new_lines.append(f"  {val}")
                    changed = True
                    continue

                # Has a block scalar — check if it's the right one
                current_scalar = re.match(r"[|>][-+]?", rest)
                scalar = current_scalar.group(0) if current_scalar else rest
                if scalar != expected:
                    new_lines.append(f"{key}: {expected}")
                    changed = True
                else:
                    new_lines.append(line)

            if changed:
                new_fm = "\n".join(new_lines)
                new_content = "---\n" + new_fm + "\n---" + content[match.end() :]
                if dry_run:
                    print(f"Would fix: {location.relative_to(root_dir)}")
                else:
                    location.write_text(new_content, encoding="utf-8")
                    print(f"FIXED: {location.relative_to(root_dir)}")
                fixed_count += 1

        except Exception as e:
            print(f"Error fixing {location}: {e}")

    action = "Fixed" if not dry_run else "Would fix"
    print(f"{action} {fixed_count} files.")

    # Post-mutation verification: re-run lint after real fixes
    if fixed_count > 0 and not dry_run:
        print("Verifying with lint...")
        lint_failed = lint_skills(root_dir, skill_map)
        if lint_failed:
            print("Warning: lint still has issues after fix.", file=sys.stderr)
        return not lint_failed

    return True


def rename_skill(old_name: str, new_name: str, root_dir: Path, dry_run: bool = False) -> bool:
    """Rename a skill and cascade updates.

    Returns True if successful, False if post-verification failed.
    Exits with error for preconditions (missing skill, conflict).
    """
    registry = scan_skills(root_dir)

    if old_name not in registry.skill_map:
        print(f"Error: Skill '{old_name}' not found.", file=sys.stderr)
        sys.exit(1)

    old_location = registry.skill_map[old_name]
    if old_location.name == "skills-lock.json":
        print("Error: Cannot rename skills-lock.json entries.", file=sys.stderr)
        sys.exit(1)

    if new_name in registry.skill_map:
        print(f"Error: Skill '{new_name}' already exists.", file=sys.stderr)
        sys.exit(1)

    # 1. Rename directory
    old_dir = old_location.parent
    new_dir = old_dir.parent / new_name
    if old_dir != new_dir:
        if dry_run:
            print(
                f"Would rename: {old_dir.relative_to(root_dir)} -> {new_dir.relative_to(root_dir)}"
            )
        else:
            old_dir.rename(new_dir)
            print(f"RENAMED: {old_dir.relative_to(root_dir)} -> {new_dir.relative_to(root_dir)}")

    # 2. Update name field in the skill's own SKILL.md
    source_dir = old_dir if dry_run else new_dir
    skill_file = source_dir / "SKILL.md"
    if dry_run:
        print(f"Would update: {skill_file.relative_to(root_dir)} (name field)")
    else:
        content = skill_file.read_text(encoding="utf-8")
        content = re.sub(
            r"^(name:\s*).*$",
            rf"\g<1>{new_name}",
            content,
            count=1,
            flags=re.MULTILINE,
        )
        skill_file.write_text(content, encoding="utf-8")
        print(f"UPDATED: {skill_file.relative_to(root_dir)} (name field)")

    # 3. Update references in other skills
    # In dry-run mode, use the original skill_map (no rename happened)
    # In real mode, re-scan to get new paths
    skill_map = registry.skill_map if dry_run else scan_skills(root_dir).skill_map
    updated_count = 0

    for _, location in skill_map.items():
        if location.name == "skills-lock.json":
            continue

        # Skip the renamed skill itself (already handled)
        if location.parent == new_dir:
            continue

        content = location.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not match:
            continue

        fm_text = match.group(1)
        new_fm = fm_text
        for field in ["depends-on", "manage", "managed-by"]:
            new_fm = re.sub(
                rf"({field}:\s*\[.*?)\b{re.escape(old_name)}\b(.*?\])",
                rf"\g<1>{new_name}\g<2>",
                new_fm,
            )
            new_fm = re.sub(
                rf"^({field}:\s*){re.escape(old_name)}\s*$",
                rf"\g<1>{new_name}",
                new_fm,
                flags=re.MULTILINE,
            )
            new_fm = re.sub(
                rf"^(\s*-\s*){re.escape(old_name)}\s*$",
                rf"\g<1>{new_name}",
                new_fm,
                flags=re.MULTILINE,
            )

        if new_fm != fm_text:
            if dry_run:
                print(f"Would update: {location.relative_to(root_dir)}")
            else:
                new_content = "---\n" + new_fm + "\n---" + content[match.end() :]
                location.write_text(new_content, encoding="utf-8")
                print(f"UPDATED REFERENCES: {location.relative_to(root_dir)}")
            updated_count += 1

    if dry_run:
        print(f"Would update {updated_count} referencing skills.")
    else:
        print(f"Rename complete. {updated_count} referencing skills updated.")
        # Post-mutation verification: re-run check after real rename
        if updated_count > 0:
            print("Verifying with check...")
            registry = scan_skills(root_dir)
            check_failed = check_all_dependencies(root_dir, registry.skill_map)
            if check_failed:
                print("Warning: check still has issues after rename.", file=sys.stderr)
            return not check_failed

    return True


DESCRIPTION_BUDGET = 300
TRIGGER_PATTERN = re.compile(r"trigger|use when|when the user", re.IGNORECASE)


def sync_skill(skill_path: Path, dry_run: bool = False) -> bool:
    """Generate agents/openai.yaml from SKILL.md canonical frontmatter.

    Returns True if generation succeeded.
    """
    skill_dir = skill_path.parent
    agents_dir = skill_dir / "agents"
    openai_yaml = agents_dir / "openai.yaml"

    try:
        content = skill_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"ERROR: Cannot read {skill_path}: {e}")
        return False

    fm = parse_frontmatter(content)
    if not fm:
        print(f"ERROR: {skill_path} has invalid frontmatter")
        return False

    name = fm.get("name")
    description = fm.get("description", "")
    disable_invocation = fm.get("disable-model-invocation", False)

    if not name:
        print(f"ERROR: {skill_path} has no name field")
        return False

    # Map: disable-model-invocation: true → allow_implicit_invocation: false
    allow_implicit = not disable_invocation

    if not HAS_YAML:
        print("ERROR: pyyaml is required for sync. Install with: uv add pyyaml")
        return False

    yaml_content = {
        "interface": {
            "display_name": str(name),
            "short_description": str(description),
        },
        "policy": {
            "allow_implicit_invocation": allow_implicit,
        },
    }

    output = yaml.dump(yaml_content, default_flow_style=False, sort_keys=False, allow_unicode=True)  # pyright: ignore[reportPossiblyUnboundVariable]

    if dry_run:
        rel = agents_dir.relative_to(skill_dir.parent.parent) / "openai.yaml"
        print(f"\n--- Would generate: {rel}")
        print(output.rstrip())
        return True

    agents_dir.mkdir(parents=True, exist_ok=True)
    try:
        openai_yaml.write_text(output, encoding="utf-8")
        target = skill_path.parent.parent.parent
        rel = openai_yaml.relative_to(target) if target.exists() else openai_yaml
        print(f"GENERATED: {rel}")
    except Exception as e:
        print(f"ERROR: Failed to write {openai_yaml}: {e}")
        return False

    return True


def sync_all(root_dir: Path, dry_run: bool = False) -> bool:
    """Run sync for all skills under skills/ directory."""
    skills_dir = root_dir / "skills"
    if not skills_dir.exists():
        print("No skills/ directory found.")
        return True

    if not HAS_YAML:
        print("ERROR: pyyaml is required for sync. Install with: uv add pyyaml")
        return False

    ok = True
    for skill_file in sorted(skills_dir.rglob("SKILL.md")):
        # Skip sub-skills (they're not standalone skills)
        if "/subskills/" in str(skill_file):
            continue
        if not sync_skill(skill_file, dry_run=dry_run):
            ok = False

    return ok


def context_check_all(
    root_dir: Path,
    json_output: bool = False,
    show_over: bool = False,
) -> bool:
    """Enforce context-load policy on all skills under skills/.

    Returns True if no hard gate failures.
    """
    skills_dir = root_dir / "skills"
    if not skills_dir.exists():
        if json_output:
            print(json.dumps({"pass": [], "fail": [], "warn": []}))
        else:
            print("No skills/ directory found.")
        return True

    results: dict[str, list[dict[str, object]]] = {"pass": [], "fail": [], "warn": []}
    has_failures = False

    for skill_file in sorted(skills_dir.rglob("SKILL.md")):
        try:
            content = skill_file.read_text(encoding="utf-8")
        except Exception:
            continue

        fm = parse_frontmatter(content)
        skill_name = str(fm.get("name", skill_file.parent.name)) if fm else skill_file.parent.name
        rel_path = str(skill_file.parent.relative_to(root_dir))

        if not fm:
            results["fail"].append(
                {"skill": skill_name, "path": rel_path, "reason": "Invalid frontmatter"}
            )
            has_failures = True
            continue

        description = fm.get("description", "")
        if isinstance(description, str):
            description = description.strip()
        else:
            description = ""

        # Hard gate: description present and non-empty
        if not description:
            results["fail"].append(
                {
                    "skill": skill_name,
                    "path": rel_path,
                    "reason": "description missing or empty",
                }
            )
            has_failures = True
            continue

        # Hard gate: description within budget
        desc_len = len(description)
        if desc_len > DESCRIPTION_BUDGET:
            results["fail"].append(
                {
                    "skill": skill_name,
                    "path": rel_path,
                    "reason": f"description is {desc_len} chars (limit: {DESCRIPTION_BUDGET})",
                    "chars": desc_len,
                }
            )
            has_failures = True
            if show_over:
                print(f"\n{skill_name} ({desc_len}/{DESCRIPTION_BUDGET} chars):")
                print(f"  {description}")
            continue

        # Soft warning: trigger vocabulary
        # Skip check for managed-by subskills — the model can't discover
        # them autonomously, so trigger vocabulary serves no purpose.
        metadata = fm.get("metadata", {})
        is_managed = bool(metadata.get("managed-by")) if isinstance(metadata, dict) else False
        if not is_managed:
            has_trigger = bool(TRIGGER_PATTERN.search(description))
            if not has_trigger:
                results["warn"].append(
                    {
                        "skill": skill_name,
                        "path": rel_path,
                        "reason": "description lacks trigger vocabulary"
                        ' -- consider adding "Use when..."',
                    }
                )

        results["pass"].append({"skill": skill_name, "path": rel_path, "chars": desc_len})

    if json_output:
        print(json.dumps(results, indent=2))
    else:
        for entry in results["pass"]:
            print(f"PASS  {entry['skill']:<30} ({entry['chars']} chars)")
        for entry in results["fail"]:
            print(f"FAIL  {entry['skill']:<30} {entry['reason']}")
        for entry in results["warn"]:
            print(f"WARN  {entry['skill']:<30} {entry['reason']}")
        print(
            f"\n{len(results['pass'])} passed,"
            f" {len(results['fail'])} failed,"
            f" {len(results['warn'])} warnings"
        )

    return not has_failures


def main():
    parser = argparse.ArgumentParser(description="LSZ Skill Management Tool")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory",
    )

    subparsers = parser.add_subparsers(dest="command", help="Subcommands")
    subparsers.add_parser("check", help="Validate all skill dependencies")

    rel_parser = subparsers.add_parser(
        "related",
        aliases=["callers"],
        help="Show inbound/outbound dependencies",
    )
    rel_parser.add_argument("skill", help="Target skill name")

    subparsers.add_parser("lint", help="Check skill frontmatter quality")
    fix_parser = subparsers.add_parser("fix", help="Automatically fix frontmatter issues")
    fix_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without modifying files",
    )

    ren_parser = subparsers.add_parser("rename", help="Rename a skill and cascade updates")
    ren_parser.add_argument("old_name", help="Current skill name")
    ren_parser.add_argument("new_name", help="New skill name")
    ren_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be renamed without modifying files",
    )

    sync_parser = subparsers.add_parser("sync", help="Generate agents/openai.yaml from SKILL.md")
    sync_parser.add_argument(
        "skill",
        nargs="?",
        help="Target skill name (omit for all)",
    )
    sync_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated",
    )

    cc_parser = subparsers.add_parser("context-check", help="Enforce context-load policy")
    cc_parser.add_argument(
        "skill",
        nargs="?",
        help="Target skill name (omit for all)",
    )
    cc_parser.add_argument(
        "--json",
        action="store_true",
        help="Machine-readable output",
    )
    cc_parser.add_argument(
        "--show-over",
        action="store_true",
        help="Print full description text for skills exceeding budget",
    )

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    root = args.project_root.resolve()
    registry = scan_skills(root)
    skill_map = registry.skill_map
    dependency_graph = registry.dependency_graph

    if args.command == "check":
        sys.exit(1 if check_all_dependencies(root, skill_map) else 0)
    elif args.command in ["related", "callers"]:
        show_related(args.skill, root, skill_map, dependency_graph)
    elif args.command == "lint":
        sys.exit(1 if lint_skills(root, skill_map) else 0)
    elif args.command == "fix":
        fix_ok = fix_skills(root, skill_map, dry_run=args.dry_run)
        sys.exit(0 if fix_ok else 1)
    elif args.command == "rename":
        rename_ok = rename_skill(args.old_name, args.new_name, root, dry_run=args.dry_run)
        sys.exit(0 if rename_ok else 1)
    elif args.command == "sync":
        if hasattr(args, "skill") and args.skill:
            skill_path = skill_map.get(args.skill)
            if not skill_path:
                print(f"Error: Skill '{args.skill}' not found.")
                sys.exit(1)
            ok = sync_skill(skill_path, dry_run=args.dry_run)
        else:
            ok = sync_all(root, dry_run=args.dry_run)
        sys.exit(0 if ok else 1)
    elif args.command == "context-check":
        ok = context_check_all(root, json_output=args.json, show_over=args.show_over)
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
