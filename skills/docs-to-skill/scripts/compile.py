#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0", "rich>=13.0.0"]
# ///
"""
Deterministic compiler for docs-to-skill pipeline.

Commands:
  validate-triggers <triggers.yaml>  - Validate trigger file
  validate-skill <skill-dir>         - Validate generated skill
  curate-refs <doc-dir> --output     - Curate reference files
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from rich.box import ROUNDED
from rich.console import Console
from rich.table import Table

console = Console()


def validate_yaml_file(file_path: Path) -> tuple[dict | None, list[str]]:
    """Validate YAML file syntax and return content."""
    issues = []

    if not file_path.exists():
        issues.append(f"File does not exist: {file_path}")
        return None, issues

    try:
        content = file_path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
        return data, issues
    except yaml.YAMLError as e:
        issues.append(f"YAML syntax error in {file_path}: {e}")
        return None, issues


def validate_triggers(triggers_data: dict) -> dict[str, Any]:
    """Validate triggers.yaml content."""
    result = {
        "valid": True,
        "issues": [],
        "warnings": [],
        "stats": {},
    }

    if not triggers_data:
        result["valid"] = False
        result["issues"].append("Empty triggers file")
        return result

    all_triggers: set[str] = set()
    module_trigger_counts: dict[str, int] = {}

    for module, triggers in triggers_data.get("triggers", {}).items():
        module_triggers: list[str] = []

        for category in ["types", "functions", "queries", "problems"]:
            category_triggers = triggers.get(category, [])
            if not isinstance(category_triggers, list):
                result["issues"].append(f"Module '{module}' category '{category}' is not a list")
                result["valid"] = False
                continue

            for trigger in category_triggers:
                if not isinstance(trigger, str):
                    result["issues"].append(
                        f"Module '{module}' has non-string trigger: {trigger}"
                    )
                    result["valid"] = False
                    continue

                # Check for regex patterns
                if re.search(r"[.*+?^${}()|[\]\\]", trigger):
                    result["issues"].append(
                        f"Module '{module}' trigger contains regex: '{trigger}'"
                    )
                    result["valid"] = False

                # Check for duplicates across modules
                if trigger.lower() in all_triggers:
                    result["warnings"].append(f"Duplicate trigger: '{trigger}'")

                all_triggers.add(trigger.lower())
                module_triggers.append(trigger)

        module_trigger_counts[module] = len(module_triggers)

        # Check trigger count per module
        count = len(module_triggers)
        if count < 10:
            result["warnings"].append(
                f"Module '{module}' has only {count} triggers (recommended: 10-30)"
            )
        elif count > 30:
            result["warnings"].append(
                f"Module '{module}' has {count} triggers (recommended: 10-30)"
            )

    result["stats"] = {
        "modules": len(triggers_data.get("triggers", {})),
        "total_triggers": len(all_triggers),
        "per_module": module_trigger_counts,
    }

    return result


def validate_skill_md(skill_file: Path) -> dict[str, Any]:
    """Validate a SKILL.md file."""
    result = {
        "valid": True,
        "issues": [],
        "warnings": [],
        "stats": {},
    }

    if not skill_file.exists():
        result["valid"] = False
        result["issues"].append(f"SKILL.md does not exist: {skill_file}")
        return result

    content = skill_file.read_text(encoding="utf-8")
    lines = content.split("\n")
    line_count = len(lines)

    result["stats"]["line_count"] = line_count

    # Check line count
    if line_count > 600:
        result["issues"].append(f"SKILL.md has {line_count} lines (max: 600)")
        result["valid"] = False
    elif line_count > 500:
        result["warnings"].append(f"SKILL.md has {line_count} lines (recommended: <=500)")

    # Check YAML frontmatter
    if not content.startswith("---"):
        result["valid"] = False
        result["issues"].append("SKILL.md missing YAML frontmatter")
        return result

    # Extract frontmatter
    frontmatter_end = content.find("---", 3)
    if frontmatter_end == -1:
        result["valid"] = False
        result["issues"].append("SKILL.md has unclosed frontmatter")
        return result

    frontmatter_text = content[3:frontmatter_end]
    try:
        frontmatter = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError as e:
        result["valid"] = False
        result["issues"].append(f"Invalid YAML frontmatter: {e}")
        return result

    # Check required fields
    if "name" not in frontmatter:
        result["valid"] = False
        result["issues"].append("Missing 'name' in frontmatter")

    if "description" not in frontmatter:
        result["valid"] = False
        result["issues"].append("Missing 'description' in frontmatter")
    elif len(frontmatter["description"]) > 1024:
        result["valid"] = False
        result["issues"].append(
            f"Description too long: {len(frontmatter['description'])} chars (max: 1024)"
        )

    # Check name matches directory
    if "name" in frontmatter:
        expected_dir = skill_file.parent.name
        if frontmatter["name"] != expected_dir:
            result["warnings"].append(
                f"Name '{frontmatter['name']}' doesn't match directory '{expected_dir}'"
            )

    # Check internal links
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    for match in link_pattern.finditer(content):
        link = match.group(2)
        if link.startswith("http") or link.startswith("#"):
            continue

        # Check relative links
        link_path = skill_file.parent / link
        if not link_path.exists():
            result["warnings"].append(f"Broken link: {link}")

    result["stats"]["frontmatter"] = frontmatter

    return result


def validate_skill_directory(skill_dir: Path) -> dict[str, Any]:
    """Validate a generated skill directory."""
    result = {
        "valid": True,
        "issues": [],
        "warnings": [],
        "stats": {},
    }

    if not skill_dir.exists():
        result["valid"] = False
        result["issues"].append(f"Skill directory does not exist: {skill_dir}")
        return result

    # Check main SKILL.md
    main_skill = skill_dir / "SKILL.md"
    main_result = validate_skill_md(main_skill)
    result["issues"].extend(main_result["issues"])
    result["warnings"].extend(main_result["warnings"])
    result["stats"]["main_skill_lines"] = main_result["stats"].get("line_count", 0)

    if not main_result["valid"]:
        result["valid"] = False

    # Check for old sub-skills structure (deprecated)
    sub_skills_dir = skill_dir / "skills"
    if sub_skills_dir.exists():
        result["warnings"].append(
            "Found 'skills/' directory — sub-skills are deprecated. Use flat structure with references/<module>.md"
        )
        sub_results = []
        for sub_skill_md in sub_skills_dir.rglob("SKILL.md"):
            sub_result = validate_skill_md(sub_skill_md)
            sub_results.append(
                {
                    "name": sub_skill_md.parent.name,
                    "valid": sub_result["valid"],
                    "issues": sub_result["issues"],
                    "warnings": sub_result["warnings"],
                    "stats": sub_result["stats"],
                }
            )
            if not sub_result["valid"]:
                result["valid"] = False
            result["issues"].extend(sub_result["issues"])
            result["warnings"].extend(sub_result["warnings"])

        result["stats"]["sub_skills_count"] = len(sub_results)

    # Check references directory
    refs_dir = skill_dir / "references"
    if refs_dir.exists():
        # Count merged reference files (direct .md files, not in subdirectories)
        merged_refs = list(refs_dir.glob("*.md"))
        result["stats"]["reference_files"] = len(merged_refs)

        # Check for raw docs (should be <skill-name>-raw/ or raw/, or any *-raw/ pattern)
        skill_name = skill_dir.name
        raw_dir = refs_dir / f"{skill_name}-raw"
        if not raw_dir.exists():
            raw_dir = refs_dir / "raw"
        if not raw_dir.exists():
            # Look for any *-raw directory
            raw_dirs = [d for d in refs_dir.iterdir() if d.is_dir() and d.name.endswith("-raw")]
            if raw_dirs:
                raw_dir = raw_dirs[0]
        if raw_dir.exists():
            raw_files = list(raw_dir.rglob("*.md"))
            result["stats"]["raw_docs_files"] = len(raw_files)
            result["stats"]["raw_docs_dir"] = raw_dir.name
        else:
            result["warnings"].append("No raw docs found (expected references/<skill-name>-raw/ or references/raw/)")

        # Check reference file metadata headers and quality
        for ref_file in merged_refs:
            content = ref_file.read_text()
            lines = len(content.split("\n"))
            result["stats"][f"ref_{ref_file.stem}_lines"] = lines

            # Check mandatory metadata header
            has_version = "**Version:**" in content or "- **Version:**" in content
            has_date = "**Date:**" in content or "- **Date:**" in content
            has_source = "**Source:**" in content or "- **Source:**" in content
            has_brief = "**Brief:**" in content or "- **Brief:**" in content

            if not has_version:
                result["issues"].append(f"Reference file missing Version: {ref_file.name}")
            if not has_date:
                result["issues"].append(f"Reference file missing Date: {ref_file.name}")
            if not has_source:
                result["warnings"].append(f"Reference file missing Source: {ref_file.name}")
            if not has_brief:
                result["warnings"].append(f"Reference file missing Brief: {ref_file.name}")
    else:
        result["warnings"].append("No references/ directory found")

    # Check for $SKILL_DIR path usage
    main_content = main_skill.read_text() if main_skill.exists() else ""
    if "../../references/" in main_content or "../references/" in main_content:
        result["warnings"].append("Found relative paths like '../../references/'. Use '$SKILL_DIR/references/' instead.")

    return result


def curate_references(doc_dir: Path, output_dir: Path) -> dict[str, Any]:
    """Curate reference files from documentation directory."""
    result = {
        "success": True,
        "files_processed": 0,
        "files_created": 0,
        "issues": [],
    }

    output_dir.mkdir(parents=True, exist_ok=True)

    for md_file in doc_dir.rglob("*.md"):
        result["files_processed"] += 1

        try:
            content = md_file.read_text(encoding="utf-8")

            # Remove empty anchor spans
            content = re.sub(r'<span id="[^"]+"></span>', "", content)

            # Remove empty divs
            content = re.sub(r'<div id="[^"]+"></div>', "", content)

            # Reduce excessive blank lines
            content = re.sub(r"\n{3,}", "\n\n", content)

            # Check for code blocks without language
            if re.search(r"```\s*\n", content):
                result["issues"].append(
                    f"Code block without language in {md_file.relative_to(doc_dir)}"
                )

            # Write to output
            rel_path = md_file.relative_to(doc_dir)
            out_path = output_dir / rel_path
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(content, encoding="utf-8")
            result["files_created"] += 1

        except Exception as e:
            result["issues"].append(f"Error processing {md_file}: {e}")

    return result


def print_validation_result(result: dict[str, Any], title: str):
    """Print validation result as a table."""
    console.print(f"\n[bold]{title}[/bold]")

    status = "[green]VALID[/green]" if result.get("valid", result.get("success")) else "[red]INVALID[/red]"
    console.print(f"Status: {status}")

    if result.get("stats"):
        table = Table(title="Statistics", box=ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        for key, value in result["stats"].items():
            if not isinstance(value, dict):
                table.add_row(key, str(value))

        console.print(table)

    if result.get("issues"):
        console.print("\n[red]Issues:[/red]")
        for issue in result["issues"]:
            console.print(f"  [red]✗[/red] {issue}")

    if result.get("warnings"):
        console.print("\n[yellow]Warnings:[/yellow]")
        for warning in result["warnings"]:
            console.print(f"  [yellow]![/yellow] {warning}")


def main():
    parser = argparse.ArgumentParser(description="Docs-to-skill compiler")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # validate-triggers
    triggers_parser = subparsers.add_parser("validate-triggers", help="Validate triggers.yaml")
    triggers_parser.add_argument("triggers_file", type=Path, help="triggers.yaml file path")

    # validate-skill
    skill_parser = subparsers.add_parser("validate-skill", help="Validate skill directory")
    skill_parser.add_argument("skill_dir", type=Path, help="Skill directory path")

    # curate-refs
    curate_parser = subparsers.add_parser("curate-refs", help="Curate reference files")
    curate_parser.add_argument("doc_dir", type=Path, help="Documentation directory")
    curate_parser.add_argument("--output", type=Path, required=True, help="Output directory")

    args = parser.parse_args()

    if args.command == "validate-triggers":
        data, issues = validate_yaml_file(args.triggers_file)
        if issues:
            console.print("[red]Failed to load triggers file:[/red]")
            for issue in issues:
                console.print(f"  {issue}")
            sys.exit(1)

        result = validate_triggers(data)
        print_validation_result(result, "Triggers Validation")

    elif args.command == "validate-skill":
        result = validate_skill_directory(args.skill_dir)
        print_validation_result(result, "Skill Validation")

    elif args.command == "curate-refs":
        result = curate_references(args.doc_dir, args.output)
        console.print(f"\n[bold]Reference Curation[/bold]")
        console.print(f"Files processed: {result['files_processed']}")
        console.print(f"Files created: {result['files_created']}")

        if result["issues"]:
            console.print("\n[yellow]Issues:[/yellow]")
            for issue in result["issues"]:
                console.print(f"  [yellow]![/yellow] {issue}")

    if result.get("valid") is False:
        sys.exit(1)


if __name__ == "__main__":
    main()
