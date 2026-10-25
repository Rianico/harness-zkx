"""Tests for the context-size gates in compile.py validate_skill_directory."""

import sys
from pathlib import Path

_scripts_path = (
    Path(__file__).parent.parent.parent / "skills" / "docs-scraper" / "scripts"
).resolve()
if str(_scripts_path) not in sys.path:
    sys.path.insert(0, str(_scripts_path))

from compile import validate_skill_directory

_HEADER = (
    "# Demo — Basics\n\n"
    "- **Version:** 1.0\n- **Date:** 2026-01-01\n"
    "- **Source:** https://example.com\n- **Brief:** basics.\n\n"
)


def _make_skill(tmp_path: Path, curated_size: int, raw_size: int) -> Path:
    skill = tmp_path / "skills" / "demo"
    refs = skill / "references"
    raw = refs / "demo-raw" / "docs"
    raw.mkdir(parents=True)
    _ = (skill / "SKILL.md").write_text(
        "---\nname: demo\ndescription: test skill.\n---\n# Demo\n", encoding="utf-8"
    )
    _ = (refs / "basics.md").write_text(_HEADER + "x" * curated_size, encoding="utf-8")
    _ = (raw / "intro.md").write_text("# Intro\n" + "y" * raw_size, encoding="utf-8")
    return skill


class TestLayerBalance:
    def test_curated_outgrowing_raw_warns(self, tmp_path: Path) -> None:
        skill = _make_skill(tmp_path, curated_size=20_000, raw_size=100)
        result = validate_skill_directory(skill)
        assert any("outgrows raw layer" in w for w in result["warnings"])
        curated = result["stats"]["curated_bytes"]
        raw = result["stats"]["raw_bytes"]
        assert isinstance(curated, int) and isinstance(raw, int)
        assert curated > raw

    def test_lean_curated_layer_passes_silently(self, tmp_path: Path) -> None:
        skill = _make_skill(tmp_path, curated_size=100, raw_size=20_000)
        result = validate_skill_directory(skill)
        assert not any("outgrows raw layer" in w for w in result["warnings"])
        curated = result["stats"]["curated_bytes"]
        raw = result["stats"]["raw_bytes"]
        assert isinstance(curated, int) and isinstance(raw, int)
        assert curated < raw

    def test_balance_warning_never_blocks(self, tmp_path: Path) -> None:
        skill = _make_skill(tmp_path, curated_size=20_000, raw_size=100)
        result = validate_skill_directory(skill)
        assert any("outgrows raw layer" in w for w in result["warnings"])
        assert not any("outgrows" in i for i in result["issues"])
