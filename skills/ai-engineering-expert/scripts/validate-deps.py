#!/usr/bin/env python3
"""
LSZ Skill Management Tool (validate-deps.py)
A versatile script for validating, linting, and fixing LSZ skill metadata.
"""
import sys
import json
import re
import argparse
from pathlib import Path

try:
    import frontmatter
except ImportError:
    print("Error: 'python-frontmatter' library not found. Install it with 'uv add --dev python-frontmatter'.")
    sys.exit(1)

def scan_skills(root_dir):
    skills_dir = Path(root_dir) / "skills"
    dependency_graph = {}
    skill_map = {}

    if skills_dir.exists():
        for skill_file in skills_dir.glob("**/SKILL.md"):
            try:
                post = frontmatter.load(skill_file)
                if 'name' not in post:
                    continue
                
                name = post['name']
                skill_map[name] = skill_file
                
                metadata = post.get('metadata', {})
                dependencies = metadata.get('depends-on', [])
                
                if isinstance(dependencies, str):
                    dependencies = [dependencies]
                
                for dep in dependencies:
                    if dep not in dependency_graph:
                        dependency_graph[dep] = []
                    dependency_graph[dep].append(name)
                    
            except Exception:
                # Store the path even if it fails to parse, so we can lint/fix it
                try:
                    content = skill_file.read_text()
                    match = re.search(r"^name:\s*(.*)$", content, re.MULTILINE)
                    if match:
                        name = match.group(1).strip()
                        skill_map[name] = skill_file
                except:
                    pass

    # Also check skills-lock.json
    lock_file = Path(root_dir) / "skills-lock.json"
    if lock_file.exists():
        try:
            lock_data = json.loads(lock_file.read_text())
            lock_skills = list(lock_data.get("skills", {}).keys())
            for name in lock_skills:
                if name not in skill_map:
                    skill_map[name] = "skills-lock.json"
        except Exception as e:
            print(f"Warning: Failed to parse skills-lock.json: {e}")

    return skill_map, dependency_graph

def check_all_dependencies(skill_map):
    print("Validating all 'depends-on' entries...")
    found_errors = False
    for skill_name, location in skill_map.items():
        if location == "skills-lock.json":
            continue
            
        try:
            post = frontmatter.load(location)
            metadata = post.get('metadata', {})
            dependencies = metadata.get('depends-on', [])
            if isinstance(dependencies, str):
                dependencies = [dependencies]
            
            for dep in dependencies:
                if dep not in skill_map:
                    print(f"ERROR: Skill '{skill_name}' ({location}) depends on non-existent skill '{dep}'")
                    found_errors = True
        except Exception as e:
            print(f"Warning: Failed to parse {location} during validation: {e}")
    
    if not found_errors:
        print("All dependencies validated successfully.")
    return found_errors

def show_related(target_skill, skill_map, dependency_graph):
    location = skill_map.get(target_skill)
    if not location:
        print(f"Error: Skill '{target_skill}' not found.")
        return

    print(f"--- Skill: {target_skill} ---")
    print(f"Location: {location}")
    
    # 1. Outbound Dependencies (What it depends on)
    print("\nOutbound Dependencies (depends-on):")
    if location == "skills-lock.json":
        print("  (Managed by skills-lock.json, outbound deps not visible)")
    else:
        try:
            post = frontmatter.load(location)
            metadata = post.get('metadata', {})
            dependencies = metadata.get('depends-on', [])
            if isinstance(dependencies, str):
                dependencies = [dependencies]
            
            if not dependencies:
                print("  (None)")
            else:
                for dep in sorted(dependencies):
                    status = " [OK]" if dep in skill_map else " [MISSING]"
                    print(f"  -> {dep}{status}")
        except Exception as e:
            print(f"  Error parsing outbound deps: {e}")

    # 2. Inbound Dependencies (What depends on it)
    print("\nInbound Dependencies (callers):")
    callers = dependency_graph.get(target_skill, [])
    if not callers:
        print("  (None)")
    else:
        for caller in sorted(callers):
            caller_loc = skill_map.get(caller, "Unknown location")
            print(f"  <- {caller} ({caller_loc})")

def lint_skills(skill_map):
    print("Linting skill frontmatter...")
    found_issues = False
    for name, location in skill_map.items():
        if location == "skills-lock.json": continue
        
        try:
            content = location.read_text()
            # 1. Check for YAML validity
            try:
                post = frontmatter.load(location)
            except Exception as e:
                print(f"LINT FAIL: {location} - Invalid YAML frontmatter: {e}")
                found_issues = True
                continue

            # 2. Check required fields
            for field in ['name', 'description']:
                if field not in post:
                    print(f"LINT FAIL: {location} - Missing required field '{field}'")
                    found_issues = True
            
            # 3. Check for block scalar usage (recommended)
            match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
            if match:
                fm_text = match.group(1)
                for field in ['description', 'argument-hint']:
                    if f"{field}:" in fm_text and not re.search(rf"^{field}:\s*[|>]-?", fm_text, re.MULTILINE):
                        val = str(post.get(field, ""))
                        if ":" in val or len(val) > 80:
                            print(f"LINT WARN: {location} - Field '{field}' should use YAML block scalar (|> or >-)")
                            found_issues = True

        except Exception as e:
            print(f"Error linting {location}: {e}")
    
    if not found_issues:
        print("Lint passed.")
    return found_issues

def fix_skills(skill_map):
    print("Fixing skill frontmatter...")
    fixed_count = 0
    for name, location in skill_map.items():
        if location == "skills-lock.json": continue
        
        try:
            content = location.read_text()
            match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
            if not match: continue
            
            fm_text = match.group(1)
            lines = fm_text.splitlines()
            new_lines = []
            changed = False
            
            for line in lines:
                if line.startswith(("description:", "argument-hint:")) and not re.search(r":\s*[|>]-?", line):
                    key, val = line.split(":", 1)
                    val = val.strip()

                    # Skip if value is just a block scalar indicator (| or >)
                    # This means content is on subsequent lines
                    if val in ("|", ">", "|-", ">-", "|+", ">+"):
                        continue

                    # Unquote if wrapped in quotes
                    if (val.startswith("\"") and val.endswith("\"")) or (val.startswith("'") and val.endswith("'")):
                        val = val[1:-1]
                    val = val.replace("\\\"", "\"").replace("\\'", "'")

                    # Use literal block scalar (|) if content has newlines, folded (>-) otherwise
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
                location.write_text(new_content)
                print(f"FIXED: {location}")
                fixed_count += 1
                
        except Exception as e:
            print(f"Error fixing {location}: {e}")
    
    print(f"Fixed {fixed_count} files.")

def find_all_references(old_name: str, skill_map: dict[str, Path]) -> list[tuple[Path, str, list[str]]]:
    """Find all skills that reference old_name in their frontmatter.

    Returns list of (path, field, values) tuples where the old_name was found.
    """
    references: list[tuple[Path, str, list[str]]] = []
    for name, location in skill_map.items():
        if location == "skills-lock.json":
            continue
        try:
            content = location.read_text()
            match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
            if not match:
                continue
            post = frontmatter.load(location)
            metadata = post.get('metadata', {})

            # Check depends-on
            deps = metadata.get('depends-on', [])
            if isinstance(deps, str):
                deps = [deps]
            if old_name in deps:
                references.append((location, 'depends-on', deps))

            # Check manage (parent skill)
            manage = metadata.get('manage', [])
            if isinstance(manage, str):
                manage = [manage]
            if old_name in manage:
                references.append((location, 'manage', manage))

            # Check managed-by (sub-skill)
            managed_by = metadata.get('managed-by', '')
            if managed_by == old_name:
                references.append((location, 'managed-by', [managed_by]))

        except Exception as e:
            print(f"Warning: Failed to scan {location}: {e}")
    return references


def find_body_references(old_name: str, root_dir: str = ".") -> list[tuple[Path, int, str]]:
    """Find all occurrences of old_name in file bodies (not frontmatter).

    Uses rg for search. Returns list of (path, line_number, line_content) tuples.
    """
    import subprocess
    results: list[tuple[Path, int, str]] = []
    root = Path(root_dir)

    # Use rg to search skills and agents directories
    try:
        proc = subprocess.run(
            ["rg", "-n", "--type", "md", "-w", old_name, "skills", "agents"],
            cwd=root_dir,
            capture_output=True,
            text=True,
        )
        for line in proc.stdout.splitlines():
            # Format: path:line_num:content
            parts = line.split(":", 2)
            if len(parts) < 3:
                continue
            path_str, line_num_str, content = parts
            path = Path(path_str)
            line_num = int(line_num_str)

            # Skip frontmatter lines (lines 1 through the second ---)
            try:
                file_lines = path.read_text().splitlines()
                in_fm = False
                fm_end = 0
                for i, fl in enumerate(file_lines):
                    if i == 0 and fl.strip() == "---":
                        in_fm = True
                    elif in_fm and fl.strip() == "---":
                        fm_end = i
                        break
                if line_num <= fm_end + 1:
                    continue
            except Exception:
                pass

            results.append((path, line_num, content.strip()))
    except FileNotFoundError:
        # rg not available, skip body scanning
        pass

    return results


def rename_skill(old_name: str, new_name: str, root_dir: str = ".") -> None:
    """Rename a skill and cascade updates to all referencing skills."""
    skill_map, _ = scan_skills(root_dir)

    # Validate old exists
    if old_name not in skill_map:
        print(f"Error: Skill '{old_name}' not found.")
        sys.exit(1)
    old_location = skill_map[old_name]
    if old_location == "skills-lock.json":
        print(f"Error: Cannot rename skills-lock.json entries.")
        sys.exit(1)

    # Validate new doesn't exist
    if new_name in skill_map:
        print(f"Error: Skill '{new_name}' already exists.")
        sys.exit(1)

    # Find all references before making changes
    references = find_all_references(old_name, skill_map)

    # 1. Rename the skill directory
    old_dir = Path(old_location).parent
    new_dir = old_dir.parent / new_name
    if old_dir != new_dir:
        old_dir.rename(new_dir)
        print(f"RENAMED: {old_dir} -> {new_dir}")

    # 2. Update the skill's own name field
    new_skill_file = new_dir / "SKILL.md"
    content = new_skill_file.read_text()
    content = re.sub(
        r"^(name:\s*).*$",
        rf"\g<1>{new_name}",
        content,
        count=1,
        flags=re.MULTILINE,
    )
    new_skill_file.write_text(content)
    print(f"UPDATED: {new_skill_file} (name: {old_name} -> {new_name})")

    # 3. Update all referencing skills (frontmatter only)
    updated: list[str] = []
    for ref_path, field, values in references:
        ref_content = ref_path.read_text()
        match = re.match(r"^---\n(.*?)\n---", ref_content, re.DOTALL)
        if not match:
            continue

        fm_text = match.group(1)

        # Build the replacement pattern for the YAML list
        if field == 'managed-by':
            pattern = rf"({field}:\s*){re.escape(old_name)}(\s*$)"
            replacement = rf"\g<1>{new_name}\2"
        else:
            pattern = rf"({field}:\s*\[.*?)\b{re.escape(old_name)}\b(.*?\])"
            replacement = rf"\g<1>{new_name}\g<2>"

        new_fm = re.sub(pattern, replacement, fm_text, flags=re.MULTILINE)
        if new_fm != fm_text:
            new_ref_content = "---\n" + new_fm + "\n---" + ref_content[match.end():]
            ref_path.write_text(new_ref_content)
            updated.append(str(ref_path))
            print(f"UPDATED: {ref_path} ({field}: {old_name} -> {new_name})")

    # 4. Scan body references (informational, for LLM to handle)
    body_refs = find_body_references(new_name, root_dir)

    # 5. Print summary
    ref_names = [Path(r[0]).stem for r in references]
    updated_names = [Path(u).stem for u in updated]
    print(f"\n--- Rename Summary ---")
    print(f"Old: [{old_name}, {', '.join(ref_names)}]")
    print(f"New: [{new_name}, {', '.join(updated_names)}]")
    print(f"Total frontmatter changed: {1 + len(updated)} (skill + {len(updated)} references)")

    if body_refs:
        print(f"\n--- Body References (manual review needed) ---")
        print(f"Found {len(body_refs)} occurrence(s) of '{new_name}' in file bodies:")
        for path, line_num, line_content in body_refs:
            print(f"  {path}:{line_num}: {line_content}")
        print(f"\nThese references may need manual updates. Review each to decide.")
        sys.exit(2)


def main():
    parser = argparse.ArgumentParser(description="LSZ Skill Management Tool")
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    # check
    subparsers.add_parser("check", help="Validate all skill dependencies")

    # related
    parser_related = subparsers.add_parser("related", help="Show inbound and outbound dependencies for a skill")
    parser_related.add_argument("skill", help="Target skill name")

    # lint
    subparsers.add_parser("lint", help="Check skill frontmatter for quality")

    # fix
    subparsers.add_parser("fix", help="Automatically fix common frontmatter issues")

    # rename
    parser_rename = subparsers.add_parser("rename", help="Rename a skill and cascade updates")
    parser_rename.add_argument("old_name", help="Current skill name")
    parser_rename.add_argument("new_name", help="New skill name")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()
    skill_map, dependency_graph = scan_skills(".")

    if args.command == "check":
        sys.exit(1 if check_all_dependencies(skill_map) else 0)
    elif args.command == "related":
        show_related(args.skill, skill_map, dependency_graph)
    elif args.command == "lint":
        sys.exit(1 if lint_skills(skill_map) else 0)
    elif args.command == "fix":
        fix_skills(skill_map)
    elif args.command == "rename":
        rename_skill(args.old_name, args.new_name)

if __name__ == "__main__":
    main()
