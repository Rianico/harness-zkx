#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = ["pyyaml", "pydantic"]
# ///

"""harness-audit: inventory the skill corpus and render the pattern-extraction criteria.

Deterministic half of the pattern-extraction workload. Resolve the corpus
(``--paths`` or the default ``~/.agents/skills`` farm), walk every skill
directory (symlinks followed), parse frontmatter, and emit an inventory with
staleness ages. Load ``data/criteria.yaml`` and render the promotion bar,
verdict vocabulary, and subagent prompt template for the cross-read phase.

The model does the rest per ``references/pattern-extraction.md``: batch
thematically, dispatch one subagent per batch with the rendered prompt, merge
across batches, present verdicts, and resolve approved items in-session.
Nothing is persisted; git history is the record.

Exit codes: ``0`` ok, ``1`` bad args, ``2`` no corpus directory found.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, ClassVar

import yaml
from pydantic import BaseModel, ConfigDict, Field

DEFAULT_CORPUS = Path.home() / ".agents" / "skills"
DEFAULT_BATCH_SIZE = 12
CRITERIA_PATH = Path(__file__).resolve().parent.parent / "data" / "criteria.yaml"
PROMPT_TEMPLATE = """You are an analyst who cross-reads skills to extract patterns worth promoting.

## Input
- Skills: {batch_skills}
- Existing rules: {rules_text}

## Promotion bar (all four must hold)
{promotion_bar}

## Verdict vocabulary
{verdicts}

## Discipline
{discipline}

## Output (JSON only)
{{"candidates": [{{
  "pattern": "1-2 sentences in do-X form",
  "evidence": ["skill-name: §Section", "skill-name: §Section"],
  "violation_risk": "1 sentence",
  "verdict": "promote_to_rule | refactor_skill | merge_skills | already_covered | too_specific",
  "target": "rules/common/<file> §Section, skills/<name>, or the covering artifact",
  "confidence": "high | medium | low"
}}]}}
"""


class SkillEntry(BaseModel):
    model_config: ClassVar[ConfigDict] = {"frozen": True}

    name: str
    path: str
    real_path: str
    description: str = ""
    disabled: bool = False
    in_repo: bool = False
    files: int = 0
    total_bytes: int = 0
    mtime: str = ""
    age_days: int = 0


class Inventory(BaseModel):
    corpus: list[str] = Field(default_factory=list)
    skills: list[SkillEntry] = Field(default_factory=list)

    @property
    def first_party(self) -> int:
        return sum(1 for s in self.skills if s.in_repo)

    @property
    def third_party(self) -> int:
        return sum(1 for s in self.skills if not s.in_repo)


def parse_frontmatter(text: str) -> dict[str, Any]:
    """Parse the leading ``---`` frontmatter block; tolerate its absence."""
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        loaded = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def inventory_skill(path: Path, repo_root: Path | None) -> SkillEntry | None:
    """Build one inventory entry; return None when the entry holds no SKILL.md."""
    skill_md = path / "SKILL.md"
    if not skill_md.is_file():
        return None
    resolved = path.resolve()
    front = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    files = [p for p in resolved.rglob("*") if p.is_file() and ".git" not in p.parts]
    stat = skill_md.stat()
    age_days = max(0, (datetime.now(tz=UTC) - datetime.fromtimestamp(stat.st_mtime, tz=UTC)).days)
    return SkillEntry(
        name=str(front.get("name") or path.name),
        path=str(path),
        real_path=str(resolved),
        description=str(front.get("description") or "").strip(),
        disabled=bool(front.get("disable-model-invocation", False)),
        in_repo=repo_root is not None and resolved.is_relative_to(repo_root),
        files=len(files),
        total_bytes=sum(p.stat().st_size for p in files),
        mtime=datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(timespec="seconds"),
        age_days=age_days,
    )


def load_criteria() -> dict[str, Any]:
    """Load data/criteria.yaml; a missing or malformed file is a hard stop."""
    if not CRITERIA_PATH.is_file():
        print(f"criteria file not found: {CRITERIA_PATH}", file=sys.stderr)
        raise SystemExit(2)
    data = yaml.safe_load(CRITERIA_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "promotion_bar" not in data or "verdicts" not in data:
        print(f"criteria file malformed: {CRITERIA_PATH}", file=sys.stderr)
        raise SystemExit(2)
    return data


def render_criteria(criteria: dict[str, Any]) -> str:
    """Render the promotion bar, verdicts, and discipline as prompt blocks."""
    lines: list[str] = []
    lines.append("## Promotion bar (all must hold)")
    for item in criteria["promotion_bar"]:
        lines.append(f"- **{item['id']}:** {item['rule']}")
    lines.append("")
    lines.append("## Verdict vocabulary")
    for item in criteria["verdicts"]:
        lines.append(f"- **{item['id']}** — {item['signal']} Treatment: {item['treatment']}")
    lines.append("")
    lines.append("## Discipline")
    for rule in criteria.get("discipline", []):
        lines.append(f"- {rule}")
    return "\n".join(lines)


def render_prompt(criteria: dict[str, Any]) -> str:
    bar = "\n".join(f"- **{i['id']}:** {i['rule']}" for i in criteria["promotion_bar"])
    verdicts = "\n".join(f"- **{i['id']}** — {i['signal']}" for i in criteria["verdicts"])
    discipline = "\n".join(f"- {r}" for r in criteria.get("discipline", []))
    return PROMPT_TEMPLATE.format(
        batch_skills="<full SKILL.md text of each skill in this batch>",
        rules_text="<full text of rules/common/*.md>",
        promotion_bar=bar,
        verdicts=verdicts,
        discipline=discipline,
    )


def build_inventory(paths: list[Path]) -> Inventory:
    repo_root = Path(__file__).resolve().parents[3]
    skills: list[SkillEntry] = []
    for corpus in paths:
        for child in sorted(corpus.iterdir()):
            entry = inventory_skill(child, repo_root)
            if entry is not None:
                skills.append(entry)
    return Inventory(corpus=[str(p) for p in paths], skills=skills)


def report_text(inv: Inventory, criteria: dict[str, Any], batch_size: int) -> str:
    lines: list[str] = []
    lines.append("Pattern extraction — corpus inventory")
    lines.append("=" * 60)
    lines.append(f"Corpus: {', '.join(inv.corpus)}")
    lines.append(
        f"Skills: {len(inv.skills)} ({inv.first_party} first-party, {inv.third_party} third-party)"
    )
    stale = [s for s in inv.skills if s.age_days > 90]
    if stale:
        oldest = max(stale, key=lambda s: s.age_days)
        lines.append(
            f"Stale (>90d): {len(stale)} skills, oldest {oldest.name} at {oldest.age_days}d"
        )
    lines.append("")
    lines.append(f"{'name':<32} {'files':>5} {'kb':>7} {'age':>5}  flags")
    for s in inv.skills:
        flags = ("disabled " if s.disabled else "") + ("3rd-party" if not s.in_repo else "")
        lines.append(
            f"{s.name:<32} {s.files:>5} {s.total_bytes // 1024:>7} {s.age_days:>4}d  {flags}".rstrip()
        )
    lines.append("")
    lines.append(f"Starting batches of {batch_size} (regroup thematically before dispatch):")
    for i in range(0, len(inv.skills), batch_size):
        names = ", ".join(s.name for s in inv.skills[i : i + batch_size])
        lines.append(f"  batch {i // batch_size + 1}: {names}")
    lines.append("")
    lines.append(render_criteria(criteria))
    lines.append("")
    lines.append("Subagent prompt template (per batch):")
    lines.append("")
    lines.append(render_prompt(criteria))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    _ = parser.add_argument(
        "--paths",
        nargs="+",
        type=Path,
        default=None,
        help=f"corpus directories (default: {DEFAULT_CORPUS})",
    )
    _ = parser.add_argument("--json", action="store_true", help="machine-readable inventory")
    _ = parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="starting batch size (default 12)",
    )
    args = parser.parse_args()

    paths = args.paths or [DEFAULT_CORPUS]
    existing = [p for p in paths if p.is_dir()]
    if not existing:
        print(
            f"no corpus directory found among: {', '.join(str(p) for p in paths)}", file=sys.stderr
        )
        return 2

    criteria = load_criteria()
    inv = build_inventory(existing)
    if args.json:
        print(
            json.dumps(
                {"inventory": inv.model_dump(), "criteria": criteria},
                indent=2,
            )
        )
    else:
        print(report_text(inv, criteria, max(1, args.batch_size)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
