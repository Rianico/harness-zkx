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
from pathlib import Path

try:
    import frontmatter
    HAS_FRONTMATTER = True  # pyright: ignore[reportConstantRedefinition]
except ImportError:
    import yaml
    HAS_FRONTMATTER = False  # pyright: ignore[reportConstantRedefinition]

try:
    import yaml
    HAS_YAML = True  # pyright: ignore[reportConstantRedefinition]
except ImportError:
    HAS_YAML = False  # pyright: ignore[reportConstantRedefinition]


def parse_frontmatter(content: str) -> dict[str, object] | None:
    """Parse YAML frontmatter from markdown content.

    Uses python-frontmatter if available, otherwise falls back to targeted 
    regex extraction for fields we need.
    """
    if HAS_FRONTMATTER:
        try:
            post = frontmatter.loads(content)  # pyright: ignore[reportPossiblyUnboundVariable]
            return post.metadata
        except Exception:
            pass
            
    # Fallback/Regex parsing for robustness
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None
    fm_text = match.group(1)
    
    result: dict[str, object] = {}
    
    # Extract name
    name_match = re.search(r"^name:\s*(.+)$", fm_text, re.MULTILINE)
    if name_match:
        result["name"] = name_match.group(1).strip().strip('"').strip("'")

    # Extract description (minimal)
    desc_match = re.search(r"^description:\s*(.+)$", fm_text, re.MULTILINE)
    if desc_match:
        result["description"] = desc_match.group(1).strip().strip('"').strip("'")

    # Extract depends-on
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
            
    # Extract manage/managed-by
    manage_fields_exist = any(
        re.search(rf"^{field}:\s*", fm_text, re.MULTILINE)
        for field in ["manage", "managed-by"]
    )
    if manage_fields_exist:
        metadata_dict: dict[str, object] = {}
        result["metadata"] = metadata_dict
        for field in ["manage", "managed-by"]:
            field_match = re.search(rf"^{field}:\s*(.+)$", fm_text, re.MULTILINE)
            if field_match:
                val = field_match.group(1).strip().strip('"').strip("'")
                if val.startswith("[") and val.endswith("]"):
                    val = [v.strip().strip('"').strip("'") for v in val[1:-1].split(",")]
                metadata_dict[field] = val

    return result if result else None


def scan_skills(root_dir: Path) -> tuple[dict[str, Path], dict[str, list[str]]]:
    """Return {skill_name: path} and {dep_name: [caller_names]}."""
    skills_dir = root_dir / "skills"
    skill_map: dict[str, Path] = {}
    dependency_graph: dict[str, list[str]] = {}

    if skills_dir.exists():
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

    # Also check skills-lock.json
    lock_file = root_dir / "skills-lock.json"
    if lock_file.exists():
        try:
            lock_data = json.loads(lock_file.read_text(encoding="utf-8"))
            for name in lock_data.get("skills", {}).keys():
                if name not in skill_map:
                    skill_map[name] = lock_file
        except Exception:
            pass

    # Discover commands from commands/ directory (early-version skills)
    commands_dir = root_dir / "commands"
    if commands_dir.is_dir():
        for cmd_file in commands_dir.glob("*.md"):
            name = cmd_file.stem
            if name and name not in skill_map:
                skill_map[name] = cmd_file

    return skill_map, dependency_graph


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
                str(caller_loc.relative_to(root_dir))
                if isinstance(caller_loc, Path) else "Unknown"
            )
            print(f"  <- {caller} ({loc_str})")


def lint_skills(root_dir: Path, skill_map: dict[str, Path]) -> bool:
    print("Linting skill frontmatter...")
    found_issues = False
    for _name, location in skill_map.items():
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

            # Check for block scalar usage (recommended)
            match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
            if match:
                fm_text = match.group(1)
                for field in ["description", "argument-hint"]:
                    uses_block_scalar = re.search(
                        rf"^{field}:\s*[|>]-?", fm_text, re.MULTILINE
                    )
                    if f"{field}:" in fm_text and not uses_block_scalar:
                        val = str(fm.get(field, ""))
                        if ":" in val or len(val) > 80:
                            print(
                                f"LINT WARN:"
                                f" {location.relative_to(root_dir)}"
                                f" - Field '{field}'"
                                " should use YAML block scalar (|> or >-)"
                            )
                            found_issues = True

        except Exception as e:
            print(f"Error linting {location}: {e}")
    
    if not found_issues:
        print("Lint passed.")
    return found_issues


def fix_skills(root_dir: Path, skill_map: dict[str, Path]):
    print("Fixing skill frontmatter...")
    fixed_count = 0
    for _name, location in skill_map.items():
        if location.name == "skills-lock.json":
            continue

        try:
            content = location.read_text(encoding="utf-8")
            match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
            if not match:
                continue
            
            fm_text = match.group(1)
            lines = fm_text.splitlines()
            new_lines = []
            changed = False
            
            for line in lines:
                if line.startswith(("description:", "argument-hint:")) and not re.search(
                    r":\s*[|>]-?", line,
                ):
                    parts = line.split(":", 1)
                    if len(parts) < 2: 
                        new_lines.append(line)
                        continue
                    key, val = parts
                    val = val.strip()

                    if val in ("|", ">", "|-", ">-", "|+", ">+"):
                        new_lines.append(line)
                        continue

                    if (val.startswith('"') and val.endswith('"')) or (
                        val.startswith("'") and val.endswith("'")
                    ):
                        val = val[1:-1]
                    val = val.replace("\\\"", "\"").replace("\\'", "'")

                    if "\n" in val:
                        new_lines.append(f"{key}: |")
                        for vline in val.split("\n"):
                            new_lines.append(f"  {vline}")
                    else:
                        new_lines.append(f"{key}: >-")
                        new_lines.append(f"  {val}")
                    changed = True
                else:
                    new_lines.append(line)
            
            if changed:
                new_fm = "\n".join(new_lines)
                new_content = "---\n" + new_fm + "\n---" + content[match.end():]
                location.write_text(new_content, encoding="utf-8")
                print(f"FIXED: {location.relative_to(root_dir)}")
                fixed_count += 1
                
        except Exception as e:
            print(f"Error fixing {location}: {e}")
    
    print(f"Fixed {fixed_count} files.")


def rename_skill(old_name: str, new_name: str, root_dir: Path):
    """Rename a skill and cascade updates to all referencing skills."""
    skill_map, _ = scan_skills(root_dir)

    if old_name not in skill_map:
        print(f"Error: Skill '{old_name}' not found.")
        sys.exit(1)

    old_location = skill_map[old_name]
    if old_location.name == "skills-lock.json":
        print("Error: Cannot rename skills-lock.json entries.")
        sys.exit(1)

    if new_name in skill_map:
        print(f"Error: Skill '{new_name}' already exists.")
        sys.exit(1)

    # 1. Rename directory
    old_dir = old_location.parent
    new_dir = old_dir.parent / new_name
    if old_dir != new_dir:
        old_dir.rename(new_dir)
        print(f"RENAMED: {old_dir.relative_to(root_dir)} -> {new_dir.relative_to(root_dir)}")

    new_skill_file = new_dir / "SKILL.md"
    content = new_skill_file.read_text(encoding="utf-8")
    content = re.sub(r"^(name:\s*).*$", rf"\g<1>{new_name}", content, count=1, flags=re.MULTILINE)
    new_skill_file.write_text(content, encoding="utf-8")
    print(f"UPDATED: {new_skill_file.relative_to(root_dir)} (name field)")

    # 2. Update references in other skills
    # Re-scan to get new paths
    skill_map, _ = scan_skills(root_dir)
    updated_count = 0

    for _name, location in skill_map.items():
        if location.name == "skills-lock.json":
            continue

        content = location.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not match:
            continue
        
        fm_text = match.group(1)
        # Targeted replacement in depends-on, manage, managed-by
        new_fm = fm_text
        for field in ["depends-on", "manage", "managed-by"]:
            # Handle list format [a, b]
            new_fm = re.sub(
                rf"({field}:\s*\[.*?)\b{re.escape(old_name)}\b(.*?\])",
                rf"\g<1>{new_name}\g<2>", new_fm,
            )
            # Handle single value
            new_fm = re.sub(
                rf"^({field}:\s*){re.escape(old_name)}\s*$",
                rf"\g<1>{new_name}", new_fm, flags=re.MULTILINE,
            )
            # Handle list format - value
            new_fm = re.sub(
                rf"^(\s*-\s*){re.escape(old_name)}\s*$",
                rf"\g<1>{new_name}", new_fm, flags=re.MULTILINE,
            )

        if new_fm != fm_text:
            new_content = "---\n" + new_fm + "\n---" + content[match.end():]
            location.write_text(new_content, encoding="utf-8")
            print(f"UPDATED REFERENCES: {location.relative_to(root_dir)}")
            updated_count += 1
            
    print(f"Rename complete. {updated_count} referencing skills updated.")


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


def sync_all(
    root_dir: Path, skill_map: dict[str, Path], dry_run: bool = False
) -> bool:
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
    root_dir: Path, skill_map: dict[str, Path], json_output: bool = False
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
        skill_name = (
            str(fm.get("name", skill_file.parent.name))
            if fm else skill_file.parent.name
        )
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
            results["fail"].append({
                "skill": skill_name,
                "path": rel_path,
                "reason": f"description is {desc_len} chars (limit: {DESCRIPTION_BUDGET})",
                "chars": desc_len,
            })
            has_failures = True
            continue

        # Soft warning: trigger vocabulary
        has_trigger = bool(TRIGGER_PATTERN.search(description))
        if not has_trigger:
            results["warn"].append({
                "skill": skill_name,
                "path": rel_path,
                "reason": 'description lacks trigger vocabulary'
                    ' -- consider adding "Use when..."',
            })

        results["pass"].append(
            {"skill": skill_name, "path": rel_path, "chars": desc_len}
        )

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
    parser = argparse.ArgumentParser(
        description="LSZ Skill Management Tool"
    )
    parser.add_argument(
        "--project-root", type=Path, default=Path.cwd(),
        help="Project root directory",
    )

    subparsers = parser.add_subparsers(dest="command", help="Subcommands")
    subparsers.add_parser("check", help="Validate all skill dependencies")

    rel_parser = subparsers.add_parser(
        "related", aliases=["callers"],
        help="Show inbound/outbound dependencies",
    )
    rel_parser.add_argument("skill", help="Target skill name")

    subparsers.add_parser("lint", help="Check skill frontmatter quality")
    subparsers.add_parser("fix", help="Automatically fix frontmatter issues")

    ren_parser = subparsers.add_parser(
        "rename", help="Rename a skill and cascade updates"
    )
    ren_parser.add_argument("old_name", help="Current skill name")
    ren_parser.add_argument("new_name", help="New skill name")

    sync_parser = subparsers.add_parser(
        "sync", help="Generate agents/openai.yaml from SKILL.md"
    )
    sync_parser.add_argument(
        "skill", nargs="?",
        help="Target skill name (omit for all)",
    )
    sync_parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be generated",
    )

    cc_parser = subparsers.add_parser(
        "context-check", help="Enforce context-load policy"
    )
    cc_parser.add_argument(
        "skill", nargs="?",
        help="Target skill name (omit for all)",
    )
    cc_parser.add_argument(
        "--json", action="store_true",
        help="Machine-readable output",
    )

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    root = args.project_root.resolve()
    skill_map, dependency_graph = scan_skills(root)

    if args.command == "check":
        sys.exit(1 if check_all_dependencies(root, skill_map) else 0)
    elif args.command in ["related", "callers"]:
        show_related(args.skill, root, skill_map, dependency_graph)
    elif args.command == "lint":
        sys.exit(1 if lint_skills(root, skill_map) else 0)
    elif args.command == "fix":
        fix_skills(root, skill_map)
    elif args.command == "rename":
        rename_skill(args.old_name, args.new_name, root)
    elif args.command == "sync":
        if hasattr(args, "skill") and args.skill:
            skill_path = skill_map.get(args.skill)
            if not skill_path:
                print(f"Error: Skill '{args.skill}' not found.")
                sys.exit(1)
            ok = sync_skill(skill_path, dry_run=args.dry_run)
        else:
            ok = sync_all(root, skill_map, dry_run=args.dry_run)
        sys.exit(0 if ok else 1)
    elif args.command == "context-check":
        ok = context_check_all(root, skill_map, json_output=args.json)
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
