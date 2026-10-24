#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
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
- refs: Resolve paths referenced from skill docs (anchors and Markdown links)
"""

import argparse
import json
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

try:
    import frontmatter
    # Reason: resolved by uv run via inline script metadata; not a project dependency
except ImportError:
    print(
        "ERROR: python-frontmatter is required. Install with: uv add python-frontmatter",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    import yaml

    HAS_YAML = True
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


def scan_skills(root_dir: Path) -> SkillRegistry:
    """Scan all skill sources and return a SkillRegistry."""
    skills_dir = root_dir / "skills"
    lock_file = root_dir / "skills-lock.json"

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


REF_PUNCTUATION = ".,;:)'\"`"
"""Trailing characters stripped from an extracted reference target."""

PLACEHOLDER_MARKERS = ("<", ">", "*", "${", "...", "…")
"""Substrings marking a target as a template or a prose label, never a path."""

EXCLUDED_REF_SEGMENTS = frozenset({"results", "reference"})
"""Directories holding vendored doc dumps and captured evidence transcripts."""

SKILL_DIR_PATTERN = re.compile(r"\$SKILL_DIR(/[^\s`'\"\])]*)?")
"""`$SKILL_DIR` reference plus its optional path suffix."""

LINK_PATTERN = re.compile(r"\[[^\]]*\]\(([^)]*)\)")
"""Real Markdown link target, searched only after inline code spans are masked."""

CODE_SPAN_PATTERN = re.compile(r"(`+)(.+?)\1")
"""Inline code span, delimited by a backtick run of matching length."""

FENCE_PATTERN = re.compile(r"^[ \t]*(?P<fence>`{3,}|~{3,})")
"""Opening or closing code fence line, indentation tolerant."""

BARE_SKILL_PATH_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_.-])skills/[A-Za-z0-9_.-]+(?:/[^\s`'\")\]>]*)?"
)
"""Bare `skills/<pkg>/…` token: a monorepo-relative path leaked into prose."""

ABSOLUTE_PATH_PATTERN = re.compile(r"(?<![\w.-])/(?:Users|home)/[^\s`'\")\]]*")
"""Absolute host path, which resolves on no other machine."""

SKILL_DIR_KIND = "skill-dir"
LINK_KIND = "link"
BARE_SKILL_PATH_KIND = "bare-skill-path"
ABSOLUTE_PATH_KIND = "absolute-path"

MISSING_TARGET = "missing target"
ESCAPES_PACKAGE = "target escapes package root"
BARE_SKILL_PATH_REASON = "bare skills/ path"
ABSOLUTE_PATH_REASON = "absolute host path"


@dataclass(frozen=True)
class RefFinding:
    """One reference site: where it is, what it points at, and why it matters."""

    file: str
    line: int
    kind: str
    target: str
    reason: str


def _finding_payload(finding: RefFinding) -> dict[str, str | int]:
    """The JSON object for one finding: the four public keys, reason excluded."""
    return {
        "file": finding.file,
        "line": finding.line,
        "kind": finding.kind,
        "target": finding.target,
    }


def _iter_unfenced_lines(content: str) -> Iterator[tuple[int, str]]:
    """Yield (line number, text) for every line outside a fenced code block."""
    fence: tuple[str, int] | None = None
    for number, text in enumerate(content.splitlines(), start=1):
        match = FENCE_PATTERN.match(text)
        if fence is None:
            if match:
                marker = match.group("fence")
                fence = (marker[0], len(marker))
                continue
            yield number, text
        elif match:
            marker = match.group("fence")
            if marker[0] == fence[0] and len(marker) >= fence[1]:
                fence = None


def _mask_code_spans(text: str) -> str:
    """Blank inline code spans so a link shown as an example is not resolved."""
    return CODE_SPAN_PATTERN.sub(lambda match: " " * len(match.group(0)), text)


def _clean_target(raw: str) -> str:
    """Drop a #fragment, surrounding space, and trailing punctuation from a target."""
    target = raw.split("#", 1)[0].strip()
    while target and target[-1] in REF_PUNCTUATION:
        target = target[:-1]
    return target


def _reference_target(raw: str) -> str | None:
    """The resolvable target inside a raw match, or None for a placeholder.

    Placeholders are judged on the raw text too: punctuation stripping would turn
    an elision (`...`) into a directory path that then looks resolvable.
    """
    if _is_placeholder(_clean_target(raw)) or _is_placeholder(raw.strip().split("#", 1)[0]):
        return None
    return _clean_target(raw)


def _is_placeholder(target: str) -> bool:
    """True when a target is a template, an ellipsis, or a bare prose label."""
    if not target or target.lower() == "url":
        return True
    if any(marker in target for marker in PLACEHOLDER_MARKERS):
        return True
    return "/" not in target and "." not in target


def _is_excluded_ref_path(relative: Path) -> bool:
    """True when a document sits in a vendored dump or a captured transcript."""
    return any(part in EXCLUDED_REF_SEGMENTS or part.endswith("-raw") for part in relative.parts)


def _iter_reference_docs(root_dir: Path, skill: str | None) -> list[Path]:
    """In-scope documents: `skills/<pkg>/SKILL.md` and `skills/<pkg>/**/*.md`."""
    skills_dir = root_dir / "skills"
    base = skills_dir / skill if skill else skills_dir
    if not base.is_dir():
        return []
    return sorted(
        doc for doc in base.rglob("*.md") if not _is_excluded_ref_path(doc.relative_to(skills_dir))
    )


def _anchor_dir(doc: Path, root_dir: Path) -> Path:
    """Directory of the nearest ancestor SKILL.md that owns this document."""
    current = doc.parent
    while current.is_relative_to(root_dir):
        if (current / "SKILL.md").exists():
            return current
        current = current.parent
    return doc.parent


def _package_root(root_dir: Path, doc: Path) -> Path:
    """`skills/<pkg>` for the first path component after `skills/`."""
    parts = doc.relative_to(root_dir).parts
    if "skills" not in parts:
        return doc.parent
    package_start = parts.index("skills") + 1
    if package_start >= len(parts):
        return doc.parent
    return root_dir.joinpath(*parts[: package_start + 1])


def _scan_references(root_dir: Path, doc: Path) -> tuple[list[RefFinding], list[RefFinding], int]:
    """Collect hard failures, warnings, and the reference count for one document."""
    relative = str(doc.relative_to(root_dir))
    anchor = _anchor_dir(doc, root_dir).resolve()
    package_root = _package_root(root_dir, doc).resolve()
    failures: list[RefFinding] = []
    warnings: list[RefFinding] = []
    checked = 0

    for number, text in _iter_unfenced_lines(doc.read_text(encoding="utf-8")):
        for match in SKILL_DIR_PATTERN.finditer(text):
            target = _reference_target(f"$SKILL_DIR{match.group(1) or ''}")
            if target is None:
                continue
            checked += 1
            suffix = target.removeprefix("$SKILL_DIR").lstrip("/")
            resolved = (anchor / suffix).resolve()
            if not resolved.is_relative_to(package_root):
                failures.append(
                    RefFinding(relative, number, SKILL_DIR_KIND, target, ESCAPES_PACKAGE)
                )
            elif not resolved.exists():
                failures.append(
                    RefFinding(relative, number, SKILL_DIR_KIND, target, MISSING_TARGET)
                )

        for match in LINK_PATTERN.finditer(_mask_code_spans(text)):
            target = _reference_target(match.group(1))
            if target is None or target.startswith(("http", "#", "mailto", "<")):
                continue
            checked += 1
            if not (doc.parent / target).exists():
                failures.append(RefFinding(relative, number, LINK_KIND, target, MISSING_TARGET))

        for match in BARE_SKILL_PATH_PATTERN.finditer(text):
            target = _reference_target(match.group(0))
            if target is None:
                continue
            warnings.append(
                RefFinding(relative, number, BARE_SKILL_PATH_KIND, target, BARE_SKILL_PATH_REASON)
            )

        for match in ABSOLUTE_PATH_PATTERN.finditer(text):
            target = _reference_target(match.group(0))
            if target is None:
                continue
            warnings.append(
                RefFinding(relative, number, ABSOLUTE_PATH_KIND, target, ABSOLUTE_PATH_REASON)
            )

    return failures, warnings, checked


def refs_check(root_dir: Path, skill: str | None = None, json_output: bool = False) -> bool:
    """Resolve every reference under skills/. Return True when a hard failure exists.

    `checked` counts resolved reference targets: every `$SKILL_DIR` path and every
    Markdown link target, placeholders and skipped prefixes excluded. Warnings are
    counted separately, so they never inflate the resolved total.
    """
    if skill is not None and not (root_dir / "skills" / skill).is_dir():
        print(f"Error: Skill '{skill}' not found.", file=sys.stderr)
        return True

    failures: list[RefFinding] = []
    warnings: list[RefFinding] = []
    checked = 0
    for doc in _iter_reference_docs(root_dir, skill):
        doc_failures, doc_warnings, doc_checked = _scan_references(root_dir, doc)
        failures.extend(doc_failures)
        warnings.extend(doc_warnings)
        checked += doc_checked

    if json_output:
        payload: dict[str, object] = {
            "checked": checked,
            "failures": [_finding_payload(finding) for finding in failures],
            "warnings": [_finding_payload(warning) for warning in warnings],
        }
        print(json.dumps(payload, indent=2))
        return bool(failures)

    for failure in failures:
        print(f"REF FAIL: {failure.file}:{failure.line} — {failure.reason}: {failure.target}")
    for warning in warnings:
        print(f"REF WARN: {warning.file}:{warning.line} — {warning.reason}: {warning.target}")
    print(f"Reference check: {checked} checked, {len(failures)} failed, {len(warnings)} warnings.")
    return bool(failures)


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
    print(f"Location: {location.relative_to(root_dir)}")

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


CREDIT_KEYS = frozenset({"source", "author", "version", "note"})
"""Allowed keys per `metadata.credits` entry."""


def _lint_credit_entry(entry: object, where: str) -> list[str]:
    if not isinstance(entry, dict):
        return [f"{where} must be a mapping, got {type(entry).__name__}"]

    problems: list[str] = []
    unknown = sorted(str(k) for k in entry if k not in CREDIT_KEYS)
    if unknown:
        problems.append(f"{where} has unrecognized keys: {', '.join(unknown)}")
    if not any(str(entry.get(k) or "").strip() for k in ("source", "author")):
        problems.append(f"{where} needs a non-empty 'source' or 'author'")
    for key, value in entry.items():
        if key in CREDIT_KEYS and not isinstance(value, str):
            problems.append(f"{where} key '{key}' must be a string")
    return problems


def _check_metadata_credits(fm: dict[str, object]) -> list[str]:
    """Validate `metadata.credits` when present: a mapping or list of mappings."""
    metadata = fm.get("metadata")
    if not isinstance(metadata, dict) or "credits" not in metadata:
        return []

    credits = metadata["credits"]
    if isinstance(credits, dict):
        return _lint_credit_entry(credits, "metadata.credits")
    if isinstance(credits, list):
        problems: list[str] = []
        for idx, entry in enumerate(credits):
            problems.extend(_lint_credit_entry(entry, f"metadata.credits[{idx}]"))
        return problems
    return ["metadata.credits must be a mapping or a list of mappings"]


def _check_duplicate_skill_names(root_dir: Path) -> bool:
    """Check that no sub-skill name collides with a top-level skill name."""
    name_paths: dict[str, list[Path]] = {}
    name_managed: dict[str, list[bool]] = {}
    skills_dir = root_dir / "skills"
    if not skills_dir.exists():
        return False

    for skill_file in skills_dir.rglob("SKILL.md"):
        content = skill_file.read_text(encoding="utf-8")
        fm = parse_frontmatter(content)
        if not fm or "name" not in fm:
            continue
        name = str(fm["name"])
        is_managed = False
        metadata = fm.get("metadata", {})
        if isinstance(metadata, dict) and metadata.get("managed-by"):
            is_managed = True
        if name not in name_paths:
            name_paths[name] = []
            name_managed[name] = []
        name_paths[name].append(skill_file)
        name_managed[name].append(is_managed)

    found = False
    for name, paths in name_paths.items():
        if len(paths) < 2:
            continue
        managed_flags = name_managed[name]
        # Staged migration: allow duplicate when one side is managed subskill of programming-expert
        # and the other is top-level legacy. Emit WARN, not FAIL, to keep gate green during cutover.
        has_managed = any(managed_flags)
        has_unmanaged = any(not f for f in managed_flags)
        is_programming_migration = (
            has_managed
            and has_unmanaged
            and any(
                "programming-expert/subskills" in str(p)
                for p, m in zip(paths, managed_flags, strict=True)
                if m
            )
        )
        if is_programming_migration:
            rels = [p.relative_to(root_dir) for p in paths]
            print(
                f"LINT WARN: Skill name '{name}' has staged migration duplicate ({len(paths)} files) — managed subskill + legacy top-level:"
            )
            for rel in rels:
                print(f"  - {rel}")
            print("  → Retire legacy top-level after cutover to clear WARN.")
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
        if location.name != "SKILL.md":
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

            # Structural check: metadata.credits when present
            for problem in _check_metadata_credits(fm):
                print(f"LINT FAIL: {location.relative_to(root_dir)} - {problem}")
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
        if location.name != "SKILL.md":
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
                    _ = location.write_text(new_content, encoding="utf-8")
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


def _rewrite_flow_list(match: re.Match[str], old: str, new: str) -> str:
    """Rewrite an exact item in a flow-style list, leaving prefixed siblings intact."""
    items = [item.strip() for item in match.group(2).split(",")]
    rewritten = [new if item == old else item for item in items]
    return f"{match.group(1)}{', '.join(rewritten)}{match.group(3)}"


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
            _ = old_dir.rename(new_dir)
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
        _ = skill_file.write_text(content, encoding="utf-8")
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
                rf"^([ \t]*{field}:[ \t]*\[)([^\]]*)(\])",
                lambda m, old=old_name, new=new_name: _rewrite_flow_list(m, old, new),
                new_fm,
                flags=re.MULTILINE,
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
                _ = location.write_text(new_content, encoding="utf-8")
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
USE_WHEN_PATTERN = re.compile(r"\buse\s+(?:[a-z_\-]+\s+)?when\b", re.IGNORECASE)
DEPRECATED_TRIGGER_PATTERN = re.compile(r"\btrigger(?:\s*when|:|\b)", re.IGNORECASE)
NEGATIVE_BOUNDARY_PATTERN = re.compile(
    r"\b(do not use|don't use|not for|avoid using|defer to|instead of)\b",
    re.IGNORECASE,
)
SYMPTOM_KEYWORD_PATTERN = re.compile(
    r"\b(fail(?:ing|s|ed|ure)?|error(?:s)?|bug(?:s)?|issue(?:s)?|break(?:s|ing)?|broken|"
    r"problem(?:s)?|leak(?:s|ing)?|flak(?:y|iness)|crash(?:es|ed|ing)?|slow(?:ness)?|"
    r"stuck|timeout|bottleneck(?:s)?|regression(?:s)?|conflict(?:s)?|drift|mess(?:y)?|"
    r"dirty|legacy|refactor(?:ing)?|debug(?:ging)?|diagnos(?:e|ing|is)?|troubleshoot(?:ing)?|"
    r"investigat(?:e|ing)?|should|decid(?:e|ing|ion)?|choos(?:e|ing)?|compar(?:e|ing|ison)?|"
    r"evaluat(?:e|ing|ion)?|trade-off(?:s)?|audit(?:ing)?|review(?:ing)?|migrat(?:e|ing|ion)?|"
    r"scaffold(?:ing)?|updat(?:e|ing)?|fix(?:ing|es)?|enhanc(?:e|ing)?|validat(?:e|ing|ion)?|"
    r"test(?:ing|s)?|verif(?:y|ying|ication)?)\b",
    re.IGNORECASE,
)
# Retain TRIGGER_PATTERN as alias for backward compatibility
TRIGGER_PATTERN = USE_WHEN_PATTERN


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
        _ = openai_yaml.write_text(output, encoding="utf-8")
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

        # Check description quality standards on model-discoverable skills
        # Skip check for managed-by subskills — the model can't discover
        # them autonomously, so trigger vocabulary serves no purpose.
        metadata = fm.get("metadata", {})
        is_managed = bool(metadata.get("managed-by")) if isinstance(metadata, dict) else False
        if not is_managed:
            # 1. Required: "Use when..." condition
            has_use_when = bool(USE_WHEN_PATTERN.search(description))
            if not has_use_when:
                results["warn"].append(
                    {
                        "skill": skill_name,
                        "path": rel_path,
                        "reason": "description lacks required 'Use when...' trigger vocabulary",
                    }
                )

            # 2. Fundamental standard: Symptom keywords / problem framing
            has_symptom = bool(SYMPTOM_KEYWORD_PATTERN.search(description))
            if not has_symptom:
                results["warn"].append(
                    {
                        "skill": skill_name,
                        "path": rel_path,
                        "reason": "description lacks symptom keywords or problem-framing signals",
                    }
                )

            # 3. Deprecated TRIGGER: tag check
            if DEPRECATED_TRIGGER_PATTERN.search(description):
                results["warn"].append(
                    {
                        "skill": skill_name,
                        "path": rel_path,
                        "reason": "description contains deprecated 'TRIGGER:' tag -- remove and formulate triggers via 'Use when...' and symptom keywords",
                    }
                )

        has_negative_boundary = bool(NEGATIVE_BOUNDARY_PATTERN.search(description))
        pass_data: dict[str, object] = {"skill": skill_name, "path": rel_path, "chars": desc_len}
        if has_negative_boundary:
            pass_data["negative_boundary"] = True
        results["pass"].append(pass_data)

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
    _ = parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory",
    )

    subparsers = parser.add_subparsers(dest="command", help="Subcommands")
    _ = subparsers.add_parser("check", help="Validate all skill dependencies")

    rel_parser = subparsers.add_parser(
        "related",
        aliases=["callers"],
        help="Show inbound/outbound dependencies",
    )
    _ = rel_parser.add_argument("skill", help="Target skill name")

    _ = subparsers.add_parser("lint", help="Check skill frontmatter quality")
    fix_parser = subparsers.add_parser("fix", help="Automatically fix frontmatter issues")
    _ = fix_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without modifying files",
    )

    ren_parser = subparsers.add_parser("rename", help="Rename a skill and cascade updates")
    _ = ren_parser.add_argument("old_name", help="Current skill name")
    _ = ren_parser.add_argument("new_name", help="New skill name")
    _ = ren_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be renamed without modifying files",
    )

    sync_parser = subparsers.add_parser("sync", help="Generate agents/openai.yaml from SKILL.md")
    _ = sync_parser.add_argument(
        "skill",
        nargs="?",
        help="Target skill name (omit for all)",
    )
    _ = sync_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated",
    )

    cc_parser = subparsers.add_parser("context-check", help="Enforce context-load policy")
    _ = cc_parser.add_argument(
        "skill",
        nargs="?",
        help="Target skill name (omit for all)",
    )
    _ = cc_parser.add_argument(
        "--json",
        action="store_true",
        help="Machine-readable output",
    )
    _ = cc_parser.add_argument(
        "--show-over",
        action="store_true",
        help="Print full description text for skills exceeding budget",
    )

    refs_parser = subparsers.add_parser("refs", help="Resolve paths referenced from skill docs")
    _ = refs_parser.add_argument(
        "skill",
        nargs="?",
        help="Target skill package (omit for all)",
    )
    _ = refs_parser.add_argument(
        "--json",
        action="store_true",
        help="Machine-readable output",
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
        deps_failed = check_all_dependencies(root, skill_map)
        refs_failed = refs_check(root)
        sys.exit(1 if deps_failed or refs_failed else 0)
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
    elif args.command == "refs":
        refs_failed = refs_check(root, skill=args.skill, json_output=args.json)
        sys.exit(1 if refs_failed else 0)


if __name__ == "__main__":
    main()
