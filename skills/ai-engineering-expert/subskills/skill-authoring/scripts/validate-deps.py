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
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import frontmatter
    HAS_FRONTMATTER = True
except ImportError:
    import yaml
    HAS_FRONTMATTER = False


def parse_frontmatter(content: str) -> dict[str, object] | None:
    """Parse YAML frontmatter from markdown content.

    Uses python-frontmatter if available, otherwise falls back to targeted 
    regex extraction for fields we need.
    """
    if HAS_FRONTMATTER:
        try:
            post = frontmatter.loads(content)
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
    for field in ["manage", "managed-by"]:
        field_match = re.search(rf"^{field}:\s*(.+)$", fm_text, re.MULTILINE)
        if field_match:
            if "metadata" not in result: result["metadata"] = {}
            val = field_match.group(1).strip().strip('"').strip("'")
            if val.startswith("[") and val.endswith("]"):
                result["metadata"][field] = [v.strip().strip('"').strip("'") for v in val[1:-1].split(",")]
            else:
                result["metadata"][field] = val

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
                if not isinstance(metadata, dict): continue
                
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
            if not fm: continue
            
            metadata = fm.get("metadata", {})
            if not isinstance(metadata, dict): continue
            
            dependencies = metadata.get("depends-on", [])
            if isinstance(dependencies, str):
                dependencies = [dependencies]
            
            for dep in dependencies:
                if dep not in skill_map:
                    print(f"ERROR: Skill '{skill_name}' ({location.relative_to(root_dir)}) depends on missing skill '{dep}'")
                    found_errors = True
        except Exception as e:
            print(f"Warning: Failed to parse {location} during validation: {e}")
    
    if not found_errors:
        print("All dependencies validated successfully.")
    return found_errors


def show_related(target_skill: str, root_dir: Path, skill_map: dict[str, Path], dependency_graph: dict[str, list[str]]):
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
            loc_str = str(caller_loc.relative_to(root_dir)) if isinstance(caller_loc, Path) else "Unknown"
            print(f"  <- {caller} ({loc_str})")


def lint_skills(root_dir: Path, skill_map: dict[str, Path]) -> bool:
    print("Linting skill frontmatter...")
    found_issues = False
    for name, location in skill_map.items():
        if location.name == "skills-lock.json": continue
        
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
                    print(f"LINT FAIL: {location.relative_to(root_dir)} - Missing required field '{field}'")
                    found_issues = True
            
            # Check for block scalar usage (recommended)
            match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
            if match:
                fm_text = match.group(1)
                for field in ["description", "argument-hint"]:
                    if f"{field}:" in fm_text and not re.search(rf"^{field}:\s*[|>]-?", fm_text, re.MULTILINE):
                        val = str(fm.get(field, ""))
                        if ":" in val or len(val) > 80:
                            print(f"LINT WARN: {location.relative_to(root_dir)} - Field '{field}' should use YAML block scalar (|> or >-)")
                            found_issues = True

        except Exception as e:
            print(f"Error linting {location}: {e}")
    
    if not found_issues:
        print("Lint passed.")
    return found_issues


def fix_skills(root_dir: Path, skill_map: dict[str, Path]):
    print("Fixing skill frontmatter...")
    fixed_count = 0
    for name, location in skill_map.items():
        if location.name == "skills-lock.json": continue
        
        try:
            content = location.read_text(encoding="utf-8")
            match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
            if not match: continue
            
            fm_text = match.group(1)
            lines = fm_text.splitlines()
            new_lines = []
            changed = False
            
            for line in lines:
                if line.startswith(("description:", "argument-hint:")) and not re.search(r":\s*[|>]-?", line):
                    parts = line.split(":", 1)
                    if len(parts) < 2: 
                        new_lines.append(line)
                        continue
                    key, val = parts
                    val = val.strip()

                    if val in ("|", ">", "|-", ">-", "|+", ">+"):
                        new_lines.append(line)
                        continue

                    if (val.startswith("\"") and val.endswith("\"")) or (val.startswith("'") and val.endswith("'")):
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
    skill_map, dependency_graph = scan_skills(root_dir)

    if old_name not in skill_map:
        print(f"Error: Skill '{old_name}' not found.")
        sys.exit(1)
    
    old_location = skill_map[old_name]
    if old_location.name == "skills-lock.json":
        print(f"Error: Cannot rename skills-lock.json entries.")
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
    
    for name, location in skill_map.items():
        if location.name == "skills-lock.json": continue
        
        content = location.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not match: continue
        
        fm_text = match.group(1)
        # Targeted replacement in depends-on, manage, managed-by
        new_fm = fm_text
        for field in ["depends-on", "manage", "managed-by"]:
            # Handle list format [a, b]
            new_fm = re.sub(rf"({field}:\s*\[.*?)\b{re.escape(old_name)}\b(.*?\])", rf"\g<1>{new_name}\g<2>", new_fm)
            # Handle single value
            new_fm = re.sub(rf"^({field}:\s*){re.escape(old_name)}\s*$", rf"\g<1>{new_name}", new_fm, flags=re.MULTILINE)
            # Handle list format - value
            new_fm = re.sub(rf"^(\s*-\s*){re.escape(old_name)}\s*$", rf"\g<1>{new_name}", new_fm, flags=re.MULTILINE)

        if new_fm != fm_text:
            new_content = "---\n" + new_fm + "\n---" + content[match.end():]
            location.write_text(new_content, encoding="utf-8")
            print(f"UPDATED REFERENCES: {location.relative_to(root_dir)}")
            updated_count += 1
            
    print(f"Rename complete. {updated_count} referencing skills updated.")


def main():
    parser = argparse.ArgumentParser(description="LSZ Skill Management Tool")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="Project root directory")
    
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")
    subparsers.add_parser("check", help="Validate all skill dependencies")
    
    rel_parser = subparsers.add_parser("related", aliases=["callers"], help="Show inbound/outbound dependencies")
    rel_parser.add_argument("skill", help="Target skill name")
    
    subparsers.add_parser("lint", help="Check skill frontmatter quality")
    subparsers.add_parser("fix", help="Automatically fix frontmatter issues")
    
    ren_parser = subparsers.add_parser("rename", help="Rename a skill and cascade updates")
    ren_parser.add_argument("old_name", help="Current skill name")
    ren_parser.add_argument("new_name", help="New skill name")

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


if __name__ == "__main__":
    main()
