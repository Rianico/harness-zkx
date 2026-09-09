#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Deterministic frontmatter injector for `meta.sources` per skillsh-compose spec.

Spec: `references/skillsh-compose.md` §2 — every composed SKILL.md must include
`meta.sources: [skill.sh URLs]` as authoritative attribution (from manifest.json).
This script preserves block scalars (>-, |-) by string surgery, not yaml.safe_dump.

Owned by docs-scraper (skill generation), not individual composed skills.

Usage:
  # generic (manifest-driven, preferred)
  uv run $SKILL_DIR/scripts/inject-sources.py --skill skills/my-skill/SKILL.md --manifest .lsz/tmp/skill-compose/<run>/manifest.json
  # legacy bash-expert default (no args = 9 canonical bash sources)
  uv run $SKILL_DIR/scripts/inject-sources.py --skill skills/programming-expert/subskills/bash-expert/SKILL.md
  # explicit URLs
  uv run $SKILL_DIR/scripts/inject-sources.py --skill skills/my-skill/SKILL.md --sources https://www.skills.sh/a/b/c https://www.skills.sh/x/y/z
  # check / dry-run
  uv run $SKILL_DIR/scripts/inject-sources.py --skill skills/my-skill/SKILL.md --manifest manifest.json --check
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Default for bash-expert backward-compat (9 sources from references/sources.md)
DEFAULT_SOURCES = [
    "https://www.skills.sh/pproenca/dot-skills/shell",
    "https://www.skills.sh/wshobson/agents/bash-defensive-patterns",
    "https://www.skills.sh/sickn33/agentic-awesome-skills/bash-scripting",
    "https://www.skills.sh/rmyndharis/antigravity-skills/bash-pro",
    "https://www.skills.sh/vudovn/ag-kit/bash-linux",
    "https://www.skills.sh/sickn33/agentic-awesome-skills/linux-shell-scripting",
    "https://www.skills.sh/wshobson/agents/error-handling-patterns",
    "https://www.skills.sh/wshobson/agents/bats-testing-patterns",
    "https://github.com/sickn33/agentic-awesome-skills/blob/main/skills/os-scripting/SKILL.md",
]

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def load_sources_from_manifest(manifest_path: Path) -> list[str]:
    try:
        raw = manifest_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(f"manifest not found: {manifest_path}") from None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid JSON in manifest {manifest_path}: {e}") from e
    # manifest.json: { inputs: [{ skillsh_url, source, ... }], staged: [...] }
    urls: list[str] = []
    for inp in data.get("inputs", []):
        # prefer skillsh_url, fallback to source, then raw (for GitHub blob repo inputs)
        u = inp.get("skillsh_url") or inp.get("source") or inp.get("raw")
        if u:
            urls.append(u)
    # fallback: if inputs empty, try staged
    if not urls:
        for s in data.get("staged", []):
            u = s.get("skillsh_url") or s.get("source") or s.get("raw")
            if u:
                urls.append(u)
    if not urls:
        raise ValueError(f"No sources found in manifest {manifest_path}")
    return urls


def parse_sources(text: str) -> list[str] | None:
    m = FRONTMATTER_RE.search(text)
    if not m:
        return None
    try:
        import yaml  # type: ignore
    except ImportError as e:
        raise RuntimeError("pyyaml required") from e
    data = yaml.safe_load(m.group(1)) or {}
    meta = data.get("meta") or {}
    if not isinstance(meta, dict):
        return None
    return meta.get("sources")


def format_meta_block(sources: list[str]) -> str:
    lines = ["meta:", "  sources:"]
    for u in sources:
        lines.append(f"  - {u}")
    return "\n".join(lines) + "\n"


def ensure_sources_text(text: str, sources: list[str]) -> tuple[str, bool]:
    m = FRONTMATTER_RE.search(text)
    if not m:
        raise ValueError("No frontmatter found")
    fm = m.group(1)
    body = text[m.end() :]
    current = parse_sources(text)
    if current == sources:
        return text, False
    if "meta:" in fm:
        meta_pattern = re.compile(r"^meta:\n(?:[ ]{2}.+\n)*", re.MULTILINE)
        new_meta = format_meta_block(sources)
        if meta_pattern.search(fm):
            new_fm = meta_pattern.sub(new_meta, fm)
        else:
            new_fm = fm.rstrip() + "\n" + new_meta
    else:
        new_fm = fm.rstrip() + "\n" + format_meta_block(sources)
    return f"---\n{new_fm}---\n{body}", True


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Inject meta.sources into SKILL.md frontmatter (docs-scraper, deterministic)"
    )
    ap.add_argument(
        "--skill", type=Path, help="Path to SKILL.md (default: bash-expert for backward compat)"
    )
    ap.add_argument(
        "--manifest", type=Path, help="manifest.json from scrape.py skills staging (preferred)"
    )
    ap.add_argument("--sources", nargs="*", help="Explicit URLs (overrides manifest)")
    ap.add_argument("--sources-file", type=Path, help="File containing URLs one per line")
    ap.add_argument("--check", action="store_true", help="check only, exit 1 on mismatch")
    ap.add_argument("--dry-run", action="store_true", help="print, don't write")
    args = ap.parse_args()

    # Resolve skill path
    # Default: bash-expert (backward compat for existing workflow)
    if args.skill:
        skill_md = args.skill
    else:
        # docs-scraper SKILL_DIR is two levels up from scripts/
        docs_scraper_dir = Path(__file__).resolve().parent.parent
        # fallback to bash-expert location
        skill_md = (
            Path(docs_scraper_dir).parent / "programming-expert/subskills/bash-expert/SKILL.md"
        )
        # when run from repo root, also try relative
        if not skill_md.exists():
            skill_md = Path("skills/programming-expert/subskills/bash-expert/SKILL.md")

    if not skill_md.exists():
        print(f"SKILL.md not found: {skill_md}", file=sys.stderr)
        return 2

    # Resolve sources
    sources: list[str]
    if args.sources:
        sources = args.sources
    elif args.sources_file:
        sources = [
            l.strip()
            for l in args.sources_file.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.strip().startswith("#")
        ]
    elif args.manifest:
        sources = load_sources_from_manifest(args.manifest)
    else:
        sources = DEFAULT_SOURCES

    text = skill_md.read_text(encoding="utf-8")

    if args.check:
        current = parse_sources(text)
        if current != sources:
            print(
                f"FAIL: meta.sources mismatch in {skill_md}\n  expected: {sources}\n  got: {current}",
                file=sys.stderr,
            )
            return 1
        print(f"OK: meta.sources matches {len(sources)} URLs in {skill_md}")
        return 0

    current = parse_sources(text)
    if current == sources:
        print(f"No change needed — meta.sources already correct in {skill_md}")
        return 0
    if args.dry_run:
        print(f"Would set meta.sources in {skill_md} to {len(sources)} URLs")
        for u in sources:
            print(f"  - {u}")
        return 0

    new_text, changed = ensure_sources_text(text, sources)
    if changed:
        skill_md.write_text(new_text, encoding="utf-8")
        print(
            f"Updated {skill_md} with meta.sources ({len(sources)} URLs) — preserved block scalars"
        )
    else:
        print("No change")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
