"""Tests for audit_skill_patterns.py: inventory, criteria rendering, and CLI exits."""

import subprocess
import sys
from pathlib import Path

import audit_skill_patterns  # type: ignore[import-not-found]

SCRIPT = Path("skills/harness-audit/scripts/audit_skill_patterns.py")

SKILL_A = """---
name: alpha
description: >-
  Alpha does things. Use when alpha-shaped work appears.
---
# Alpha
Body.
"""

SKILL_B = """---
name: beta
description: Beta does other things.
disable-model-invocation: true
---
# Beta
Body.
"""


def make_skill(root: Path, name: str, body: str) -> Path:
    d = root / name
    d.mkdir(parents=True)
    _ = (d / "SKILL.md").write_text(body, encoding="utf-8")
    return d


def test_inventory_counts_skills_and_flags(tmp_path: Path) -> None:
    _ = make_skill(tmp_path, "alpha", SKILL_A)
    _ = make_skill(tmp_path, "beta", SKILL_B)
    inv = audit_skill_patterns.build_inventory([tmp_path])
    assert [s.name for s in inv.skills] == ["alpha", "beta"]
    beta = inv.skills[1]
    assert beta.disabled is True
    assert beta.description.startswith("Beta")
    assert beta.files >= 1


def test_symlinked_skill_is_resolved(tmp_path: Path) -> None:
    real = make_skill(tmp_path / "real", "alpha", SKILL_A)
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "alpha").symlink_to(real, target_is_directory=True)
    inv = audit_skill_patterns.build_inventory([corpus])
    assert len(inv.skills) == 1
    assert inv.skills[0].name == "alpha"
    assert Path(inv.skills[0].real_path) == real.resolve()


def test_non_skill_entries_are_skipped(tmp_path: Path) -> None:
    (tmp_path / "not-a-skill").mkdir()
    inv = audit_skill_patterns.build_inventory([tmp_path])
    assert inv.skills == []


def test_criteria_load_and_render() -> None:
    criteria = audit_skill_patterns.load_criteria()
    bar_ids = [i["id"] for i in criteria["promotion_bar"]]
    assert bar_ids == ["corroboration", "actionable", "violation_risk", "novelty"]
    verdict_ids = [v["id"] for v in criteria["verdicts"]]
    assert "promote_to_rule" in verdict_ids and "too_specific" in verdict_ids
    rendered = audit_skill_patterns.render_criteria(criteria)
    assert "corroboration" in rendered and "promote_to_rule" in rendered
    prompt = audit_skill_patterns.render_prompt(criteria)
    assert "JSON only" in prompt and "violation_risk" in prompt


def test_missing_corpus_exits_two() -> None:
    res = subprocess.run(
        [sys.executable, str(SCRIPT), "--paths", "no-such-dir-xyz"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 2


def test_json_output_round_trips(tmp_path: Path) -> None:
    _ = make_skill(tmp_path, "alpha", SKILL_A)
    res = subprocess.run(
        [sys.executable, str(SCRIPT), "--paths", str(tmp_path), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    payload = res.stdout
    assert '"name": "alpha"' in payload
    assert '"promotion_bar"' in payload
