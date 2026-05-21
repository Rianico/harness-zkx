#!/usr/bin/env python3
"""
LSZ Skill Dependency Scanner
Parses all SKILL.md files and identifies inbound dependencies (callers).
Handles potential YAML parsing issues in skill frontmatter.
"""
import os
import re
import sys
from pathlib import Path

# Try to import yaml, but fall back to a simple regex parser if needed
# as some SKILL.md frontmatter might have non-standard YAML.
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

def parse_frontmatter_regex(content):
    """Fallback parser for frontmatter using regex."""
    data = {}
    match = re.search(r"^name:\s*(.*)$", content, re.MULTILINE)
    if match:
        data['name'] = match.group(1).strip()
    
    # Simple extraction for depends-on: [a, b, c]
    match = re.search(r"depends-on:\s*\[(.*?)\]", content, re.DOTALL)
    if match:
        deps = [d.strip() for d in match.group(1).split(',')]
        data['metadata'] = {'depends-on': deps}
    return data

def scan_skills(root_dir):
    skills_dir = Path(root_dir) / "skills"
    if not skills_dir.exists():
        print(f"Error: {skills_dir} not found.")
        return

    dependency_graph = {}
    skill_map = {}

    for skill_file in skills_dir.glob("**/SKILL.md"):
        try:
            content = skill_file.read_text()
            # Extract frontmatter block
            match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
            if not match:
                continue
            
            frontmatter_text = match.group(1)
            data = None
            
            if HAS_YAML:
                try:
                    data = yaml.safe_load(frontmatter_text)
                except Exception:
                    # Fallback to regex if YAML fails
                    data = parse_frontmatter_regex(frontmatter_text)
            else:
                data = parse_frontmatter_regex(frontmatter_text)
            
            if not data or 'name' not in data:
                continue
            
            name = data['name']
            skill_map[name] = skill_file
            
            metadata = data.get('metadata', {})
            dependencies = metadata.get('depends-on', [])
            
            if isinstance(dependencies, str):
                dependencies = [dependencies]
            
            for dep in dependencies:
                if dep not in dependency_graph:
                    dependency_graph[dep] = []
                dependency_graph[dep].append(name)
                
        except Exception as e:
            print(f"Warning: Failed to parse {skill_file}: {e}")

    return skill_map, dependency_graph

def main():
    target_skill = sys.argv[1] if len(sys.argv) > 1 else None
    skill_map, dependency_graph = scan_skills(".")

    if target_skill:
        callers = dependency_graph.get(target_skill, [])
        if not callers:
            print(f"No inbound dependencies found for skill: {target_skill}")
        else:
            print(f"Inbound dependencies (callers) for '{target_skill}':")
            for caller in callers:
                path = skill_map.get(caller, "Unknown path")
                print(f"  - {caller} ({path})")
    else:
        print("Skill Dependency Map:")
        for dep, sorted_deps in sorted(dependency_graph.items()):
            print(f"{dep}:")
            for caller in sorted(sorted_deps):
                print(f"  <- {caller}")

if __name__ == "__main__":
    main()
