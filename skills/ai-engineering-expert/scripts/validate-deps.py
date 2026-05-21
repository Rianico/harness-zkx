#!/usr/bin/env python3
"""
LSZ Skill Dependency Scanner & Validator
Parses all SKILL.md files to validate metadata.depends-on and find inbound callers.
Checks against local skills and skills-lock.json.
"""
import sys
import json
import re
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
                    
            except Exception as e:
                print(f"Warning: Failed to parse {skill_file}: {e}")

    # Also check skills-lock.json
    lock_file = Path(root_dir) / "skills-lock.json"
    lock_skills = []
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

def check_all_dependencies(skill_map, dependency_graph):
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

def list_callers(target_skill, skill_map, dependency_graph):
    callers = dependency_graph.get(target_skill, [])
    if not callers:
        print(f"No inbound dependencies found for skill: {target_skill}")
    else:
        print(f"Inbound dependencies (callers) for '{target_skill}':")
        for caller in sorted(callers):
            location = skill_map.get(caller, "Unknown location")
            print(f"  - {caller} ({location})")

def main():
    skill_map, dependency_graph = scan_skills(".")
    if not skill_map and not dependency_graph:
        print("No skills found.")
        sys.exit(0)

    args = sys.argv[1:]
    
    if not args:
        # Default: validate all
        has_errors = check_all_dependencies(skill_map, dependency_graph)
        sys.exit(1 if has_errors else 0)
    
    command = args[0]
    
    if command == "callers" and len(args) > 1:
        list_callers(args[1], skill_map, dependency_graph)
    elif command == "--help" or command == "-h":
        print("Usage:")
        print("  uv run $SKILL_DIR/scripts/validate-deps.py                 # Validate all dependencies")
        print("  uv run $SKILL_DIR/scripts/validate-deps.py callers <name>  # List inbound dependencies")
    else:
        # Fallback to direct name search if not 'callers' but arg present
        list_callers(command, skill_map, dependency_graph)

if __name__ == "__main__":
    main()
