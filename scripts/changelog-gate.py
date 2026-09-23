#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""Deterministic floor for the changelog ledger (ADR-0016, issue #76).

Read-only: a failing run never writes the worktree, the target branch, or CHANGELOG.md.

  squash  Merge boundary. `HEAD` must be the single squashed commit; its subject must be
          conventional and project exactly one well-formed entry.
  ledger  PR boundary. The `## [Unreleased]` block must pass well-formedness, section
          integrity, duplicate-identity, placeholder, and per-scope accounting checks.

Exit codes: 0 pass · 1 blocked/fixable · 2 blocked/needs human.

Usage:
  uv run scripts/changelog-gate.py squash [--base main]
  uv run scripts/changelog-gate.py ledger [--changelog CHANGELOG.md]
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

GENERATOR = Path(__file__).resolve().with_name("changelog-unreleased.py")


def _load_generator() -> ModuleType:
    """Import the sibling generator so the gate shares its grammar and identity rule.

    `changelog-unreleased.py` owns the conventional-commit table, the section names, the
    `(#N)`-stripping identity rule, and the commit-log parser. Re-deriving any of them here
    would let the check and the renderer disagree, which is the failure this gate exists to
    stop.
    """
    spec = importlib.util.spec_from_file_location("changelog_unreleased", GENERATOR)
    if spec is None or spec.loader is None:  # pragma: no cover - importlib guarantees both
        raise RuntimeError(f"cannot load {GENERATOR}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()

# The renderer writes `* `, an optional `**scope:** `, then the subject. Anything else is
# not something `changelog-unreleased.py update` could have produced.
ENTRY_RE = re.compile(r"^\* (?:\*\*[^*]+:\*\* )?\S")
SCOPED_RE = re.compile(r"^\* \*\*[^*]+:\*\* \S")
SCOPE_RE = re.compile(r"^\* \*\*(?P<scope>[^*]+):\*\*")
EMPTY_BULLET_RE = re.compile(r"^[*+-]\s*$")
PLACEHOLDER_RE = re.compile(r"\bTBD\b|\bTODO\b|<[^>]+>")
KNOWN_SECTIONS = frozenset(section for section, _ in GEN.TYPE_SECTIONS.values())


@dataclass(frozen=True)
class Finding:
    """One failed check. `fixable` separates "edit the ledger" from "a human must look"."""

    check: str
    detail: str
    fixable: bool = True


def unreleased_block(content: str) -> str | None:
    """The `## [Unreleased]` body, up to the next version heading. None when absent."""
    if GEN.UNRELEASED_HEADING not in content:
        return None
    _, rest = content.split(GEN.UNRELEASED_HEADING, 1)
    version = GEN.VERSION_HEADING_RE.search(rest)
    return rest[: version.start()] if version else rest


def check_sections(block: str) -> list[Finding]:
    """The block parses, carries only known sections, and puts every entry under one."""
    findings: list[Finding] = []
    current: str | None = None
    seen: set[str] = set()
    for line in block.splitlines():
        heading = GEN.SECTION_HEADING_RE.match(line)
        if heading:
            name = heading.group("name")
            if name in seen:
                findings.append(Finding("section-integrity", f"duplicate heading '### {name}'"))
            seen.add(name)
            if name not in KNOWN_SECTIONS:
                findings.append(Finding("section-integrity", f"unknown section '### {name}'"))
            current = name
            continue
        if GEN.BULLET_RE.match(line) and current is None:
            findings.append(
                Finding("section-integrity", f"entry outside any section: {line.strip()!r}")
            )
    return findings


def check_entries(block: str) -> list[Finding]:
    """Every entry matches the renderer's bullet grammar and carries no placeholder."""
    findings: list[Finding] = []
    for line in block.splitlines():
        text = line.rstrip()
        if EMPTY_BULLET_RE.match(text):
            findings.append(Finding("well-formedness", f"empty bullet: {text!r}"))
            continue
        if not GEN.BULLET_RE.match(text):
            continue
        if not ENTRY_RE.match(text) or (text.startswith("* **") and not SCOPED_RE.match(text)):
            findings.append(
                Finding("well-formedness", f"not in the renderer's bullet grammar: {text!r}")
            )
        if PLACEHOLDER_RE.search(text):
            findings.append(Finding("placeholders", f"placeholder text: {text!r}"))
    return findings


def check_duplicates(sections: dict[str, list[str]]) -> list[Finding]:
    """No two entries share an identity, using the generator's `(#N)`-stripping rule."""
    findings: list[Finding] = []
    seen: set[str] = set()
    for entries in sections.values():
        for entry in entries:
            identity = GEN.entry_identity(entry)
            if identity in seen:
                findings.append(
                    Finding("duplicate-identity", f"duplicate entry identity: {identity!r}")
                )
            seen.add(identity)
    return findings


def scope_counts(entries: list[str]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for entry in entries:
        match = SCOPE_RE.match(entry.strip())
        if match:
            counts[match.group("scope").strip()] += 1
    return counts


def check_accounting(
    sections: dict[str, list[str]], generated: dict[str, list[str]]
) -> list[Finding]:
    """`entries(scope) ≤ commits(scope)`, with the global bound kept as a coarse pre-filter.

    The global count is diluted by unrelated commits: on the measured ledger `73 ≤ 263`
    held while `herdr` carried 12 entries against 3 commits. It cannot be the check. This
    counts; it never deletes, so the rejected reachability pruning is not implicated.
    """
    ledger = [entry for entries in sections.values() for entry in entries]
    minted = [entry for entries in generated.values() for entry in entries]
    findings: list[Finding] = []
    if len(ledger) > len(minted):
        findings.append(
            Finding(
                "accounting",
                f"global pre-filter: {len(ledger)} entries > {len(minted)} projected entries",
            )
        )
    ledger_scopes = scope_counts(ledger)
    minted_scopes = scope_counts(minted)
    for scope in sorted(ledger_scopes):
        if ledger_scopes[scope] > minted_scopes.get(scope, 0):
            findings.append(
                Finding(
                    "accounting",
                    f"scope {scope!r}: {ledger_scopes[scope]} entries > "
                    f"{minted_scopes.get(scope, 0)} commits",
                )
            )
    return findings


def check_ledger(changelog: Path) -> list[Finding]:
    """The whole-ledger floor. Reads; never writes."""
    if not changelog.exists():
        return [Finding("ledger", f"{changelog} is missing", fixable=False)]
    try:
        content = changelog.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        return [Finding("ledger", f"{changelog} is not UTF-8: {error}", fixable=False)]

    block = unreleased_block(content)
    if block is None:
        return [Finding("section-integrity", f"no '{GEN.UNRELEASED_HEADING}' block to check")]

    findings = check_sections(block) + check_entries(block)
    sections = GEN.parse_unreleased_sections(content)
    findings += check_duplicates(sections)

    commits = GEN.parse_commit_log(
        GEN.run(["git", "log", "HEAD", "--pretty=format:%s%n%b%x00%x00", "--no-merges"])
    )
    if not commits:
        return findings + [
            Finding("accounting", "no commits reachable from HEAD; cannot evaluate", fixable=False)
        ]
    findings += check_accounting(sections, GEN.commits_to_sections(commits))
    return findings


def default_base() -> str | None:
    """The merge target: `origin/HEAD` when it exists, else `main`, else `master`."""
    head = GEN.run(["git", "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"])
    if head:
        return head.removeprefix("refs/remotes/")
    for candidate in ("main", "master"):
        if GEN.run(["git", "rev-parse", "--verify", "--quiet", f"{candidate}^{{commit}}"]):
            return candidate
    return None


def check_squash(base: str) -> list[Finding]:
    """The merge-boundary check: one squashed commit, conventional, one well-formed entry."""
    if not GEN.run(["git", "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}"]):
        return [Finding("squash-state", f"base ref {base!r} does not resolve", fixable=False)]
    count = GEN.run(["git", "rev-list", "--count", f"{base}..HEAD"])
    if not count.isdigit():
        return [Finding("squash-state", f"cannot count commits ahead of {base!r}", fixable=False)]
    if count != "1":
        return [
            Finding(
                "squash-state",
                f"{count} commits ahead of {base!r}; the merge boundary expects exactly one",
                fixable=False,
            )
        ]

    subject = GEN.run(["git", "log", "-1", "--pretty=%s"])
    body = GEN.run(["git", "log", "-1", "--pretty=%b"])
    if not GEN.CONVENTIONAL_RE.match(subject):
        return [Finding("conventional-subject", f"not a conventional subject: {subject!r}")]

    projected = [
        entry
        for entries in GEN.commits_to_sections([(subject, body)]).values()
        for entry in entries
    ]
    if len(projected) != 1:
        return [
            Finding(
                "single-entry",
                f"subject projects {len(projected)} entries, expected exactly one: {subject!r}",
            )
        ]
    entry = projected[0]
    if not ENTRY_RE.match(entry) or (entry.startswith("* **") and not SCOPED_RE.match(entry)):
        return [Finding("well-formedness", f"projected entry is not well-formed: {entry!r}")]
    return []


def exit_code(findings: list[Finding]) -> int:
    if not findings:
        return 0
    return 2 if any(not finding.fixable for finding in findings) else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deterministic changelog-ledger floor (ADR-0016)")
    parser.add_argument("check", choices=["squash", "ledger"], help="which boundary to check")
    parser.add_argument("--changelog", default="CHANGELOG.md", help="path to CHANGELOG.md")
    parser.add_argument("--base", default=None, help="base ref for the squash check")
    args = parser.parse_args(argv)

    if args.check == "squash":
        base = args.base or default_base()
        if base is None:
            findings = [
                Finding("squash-state", "cannot resolve a base branch; pass --base", fixable=False)
            ]
        else:
            findings = check_squash(base)
    else:
        findings = check_ledger(Path(args.changelog))

    for finding in findings:
        print(f"[{finding.check}] {finding.detail}", file=sys.stderr)
    if not findings:
        print(f"{args.check}: pass")
    return exit_code(findings)


if __name__ == "__main__":
    sys.exit(main())
