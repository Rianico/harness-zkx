#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Validate structure of scraped documentation directory.

Generates a deterministic structure report including:
- File count and token estimates
- Directory hierarchy
- API surface summary
- Issues (empty files, missing indices)
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


def count_tokens_estimate(content: str) -> int:
    """Estimate token count using word count * 1.3 heuristic."""
    words = len(content.split())
    return int(words * 1.3)


def analyze_directory(doc_dir: Path) -> dict[str, Any]:
    """Analyze documentation directory structure."""
    structure: dict[str, Any] = {
        "total_files": 0,
        "total_tokens_estimate": 0,
        "directory_structure": {},
        "file_list": [],
        "issues": [],
    }

    if not doc_dir.exists():
        structure["issues"].append(f"Directory does not exist: {doc_dir}")
        return structure

    for root, dirs, files in root_walk(doc_dir):
        rel_root = Path(root).relative_to(doc_dir)
        rel_root_str = str(rel_root) if str(rel_root) != "." else ""

        md_files = [f for f in files if f.endswith(".md")]

        if not md_files:
            continue

        structure["total_files"] += len(md_files)

        dir_info: dict[str, Any] = {
            "files": len(md_files),
            "subdirs": dirs,
        }

        if rel_root_str:
            structure["directory_structure"][rel_root_str] = dir_info
        else:
            structure["directory_structure"]["."] = dir_info

        for md_file in md_files:
            file_path = Path(root) / md_file
            rel_file_path = file_path.relative_to(doc_dir)
            structure["file_list"].append(str(rel_file_path))

            try:
                content = file_path.read_text(encoding="utf-8")
                if not content.strip():
                    structure["issues"].append(f"Empty file: {rel_file_path}")
                else:
                    structure["total_tokens_estimate"] += count_tokens_estimate(content)
            except Exception as e:
                structure["issues"].append(f"Cannot read file {rel_file_path}: {e}")

    return structure


def root_walk(doc_dir: Path):
    """Walk directory, skipping hidden and common ignore patterns."""
    ignore_dirs = {".git", ".cache", "__pycache__", "node_modules", ".venv", "venv"}

    for root, dirs, files in os.walk(doc_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ignore_dirs]
        yield root, dirs, files


def extract_api_surface(doc_dir: Path) -> dict[str, list[str]]:
    """Extract API surface from documentation (types, functions, traits)."""
    import re

    api_surface: dict[str, list[str]] = {
        "types": [],
        "functions": [],
        "traits": [],
    }

    type_pattern = re.compile(r"^#+\s*`?([A-Z][a-zA-Z0-9]*)`?", re.MULTILINE)
    function_pattern = re.compile(r"###?\s*`?([a-z][a-z0-9_]*)`?", re.MULTILINE)
    trait_pattern = re.compile(r"trait\s+([A-Z][a-zA-Z0-9]*)", re.MULTILINE)

    for md_file in doc_dir.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            api_surface["types"].extend(type_pattern.findall(content))
            api_surface["functions"].extend(function_pattern.findall(content))
            api_surface["traits"].extend(trait_pattern.findall(content))
        except Exception:
            pass

    api_surface["types"] = sorted(set(api_surface["types"]))
    api_surface["functions"] = sorted(set(api_surface["functions"]))
    api_surface["traits"] = sorted(set(api_surface["traits"]))

    return api_surface


def main():
    parser = argparse.ArgumentParser(description="Validate documentation structure")
    parser.add_argument("doc_dir", type=Path, help="Documentation directory to analyze")
    parser.add_argument("--output", type=Path, help="Output JSON file path")
    parser.add_argument("--api-surface", action="store_true", help="Extract API surface")

    args = parser.parse_args()

    report = analyze_directory(args.doc_dir)

    if args.api_surface:
        report["api_surface"] = extract_api_surface(args.doc_dir)

    output_json = json.dumps(report, indent=2, ensure_ascii=False)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output_json, encoding="utf-8")
        print(f"Structure report written to: {args.output}")
    else:
        print(output_json)

    if report["issues"]:
        print(f"\nFound {len(report['issues'])} issues:", file=sys.stderr)
        for issue in report["issues"][:10]:
            print(f"  - {issue}", file=sys.stderr)
        if len(report["issues"]) > 10:
            print(f"  ... and {len(report['issues']) - 10} more", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
