#!/usr/bin/env python3
"""
LSZ Skill Dependency Scanner
Parses all SKILL.md files and identifies inbound dependencies (callers).
Uses python-frontmatter for robust Markdown metadata parsing.
"""
import sys
from pathlib import Path

try:
    import frontmatter
except ImportError:
    print("Error: 'python-frontmatter' library not found. Install it with 'uv add --dev python-frontmatter'.")
    sys.exit(1)

def scan_skills(root_dir):
    skills_dir = Path(root_dir) / "skills"
    if not skills_dir.exists():
        print(f"Error: {skills_dir} not found.")
        return

    dependency_graph = {}
    skill_map = {}

    for skill_file in skills_dir.glob("**/SKILL.md"):
        try:
            # Load the markdown file with frontmatter
            post = frontmatter.load(skill_file)
            
            if 'name' not in post:
                continue
            
            name = post['name']
            skill_map[name] = skill_file
            
            # Check metadata.depends-on
            metadata = post.get('metadata', {})
            dependencies = metadata.get('depends-on', [])
            
            if isinstance(dependencies, str):
                dependencies = [dependencies]
            
            for dep in dependencies:
                if dep not in dependency_graph:
                    dependency_graph[dep] = []
                dependency_graph[dep].append(name)
                
        except Exception as e:
            # Report the error but continue scanning other files
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
            for caller in sorted(callers):
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
