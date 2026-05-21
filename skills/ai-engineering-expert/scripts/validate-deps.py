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

if __name__ == "__main__":
    main()
