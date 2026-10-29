"""Tests for the to-skill pipeline front half (staging, sanitize, brief)."""

import sys
from pathlib import Path

_scripts_path = (
    Path(__file__).parent.parent.parent / "skills" / "docs-scraper" / "scripts"
).resolve()
if str(_scripts_path) not in sys.path:
    sys.path.insert(0, str(_scripts_path))

import pytest
from toskill import classify_input, derive_name, run_to_skill, slugify


@pytest.fixture
def doc_dir(tmp_path: Path) -> Path:
    """A small local documentation tree with one sanitized file."""
    docs = tmp_path / "docs" / "guide"
    docs.mkdir(parents=True)
    _ = (docs / "intro.md").write_text("# Intro\n\nUse widgets with care.\n", encoding="utf-8")
    _ = (docs / "dirty.md").write_text("hidden\u200bzero\n", encoding="utf-8")
    return docs.parent


class TestClassifyInput:
    def test_url_is_remote(self) -> None:
        assert classify_input("https://example.com/docs") == "remote"

    def test_existing_dir(self, doc_dir: Path) -> None:
        assert classify_input(str(doc_dir)) == "dir"

    def test_existing_file(self, doc_dir: Path) -> None:
        assert classify_input(str(doc_dir / "guide" / "intro.md")) == "file"

    def test_unknown_token_falls_back_to_remote(self) -> None:
        assert classify_input("ratatui") == "remote"


class TestDeriveName:
    def test_explicit_name_wins(self) -> None:
        assert derive_name(["ignored"], "My Skill") == "my-skill"

    def test_url_tail(self) -> None:
        assert derive_name(["https://example.com/FastAPI/"], None) == "fastapi"

    def test_local_dir_name(self, doc_dir: Path) -> None:
        assert derive_name([str(doc_dir)], None) == "docs"


class TestSlugify:
    def test_collapses_nonalnum(self) -> None:
        assert slugify("a b_c.d!") == "a-b-c-d"

    def test_empty_falls_back(self) -> None:
        assert slugify("///") == "source"


class TestRunToSkill:
    def _run(self, doc_dir: Path, tmp_path: Path, name: str = "demo") -> int:
        return run_to_skill(
            inputs=[str(doc_dir)],
            name=name,
            supplementary=[],
            output_dir=tmp_path / "out",
        )

    def test_stages_raw_and_brief(self, doc_dir: Path, tmp_path: Path) -> None:
        code = self._run(doc_dir, tmp_path)
        assert code == 0
        skill = tmp_path / "out" / "demo"
        assert (skill / "GENERATION-BRIEF.md").is_file()
        assert (skill / "structure-report.json").is_file()
        assert (skill / "references" / "demo-raw" / "docs" / "guide" / "intro.md").is_file()

    def test_sanitizes_staged_markdown(self, doc_dir: Path, tmp_path: Path) -> None:
        _ = self._run(doc_dir, tmp_path)
        dirty = (
            tmp_path / "out" / "demo" / "references" / "demo-raw" / "docs" / "guide" / "dirty.md"
        )
        assert "\u200b" not in dirty.read_text(encoding="utf-8")

    def test_brief_names_gates_and_contract(self, doc_dir: Path, tmp_path: Path) -> None:
        _ = self._run(doc_dir, tmp_path)
        brief = (tmp_path / "out" / "demo" / "GENERATION-BRIEF.md").read_text(encoding="utf-8")
        assert "compile.py validate-skill" in brief
        assert "compile.py validate-triggers" in brief
        assert "skill-template.md" in brief
        assert "skill-authoring" in brief

    def test_supplementary_staged_apart(self, doc_dir: Path, tmp_path: Path) -> None:
        supp = tmp_path / "extra.md"
        _ = supp.write_text("# Extra\n\nSupplementary material.\n", encoding="utf-8")
        code = run_to_skill(
            inputs=[str(doc_dir)],
            name="demo",
            supplementary=[str(supp)],
            output_dir=tmp_path / "out",
        )
        assert code == 0
        staged = tmp_path / "out" / "demo" / "references" / "demo-raw" / "_supplementary"
        assert (staged / "extra-md" / "extra.md").is_file()

    def test_refuses_nonempty_target(self, doc_dir: Path, tmp_path: Path) -> None:
        assert self._run(doc_dir, tmp_path) == 0
        assert self._run(doc_dir, tmp_path) == 1

    def test_empty_inputs_refused(self, tmp_path: Path) -> None:
        assert run_to_skill(inputs=[], name=None, supplementary=[], output_dir=tmp_path) == 1


class TestFoldInto:
    @pytest.fixture
    def existing_skill(self, tmp_path: Path) -> Path:
        """A skill with curated files and an initial structure report."""
        skill = tmp_path / "skills" / "demo"
        (skill / "references" / "demo-raw" / "docs").mkdir(parents=True)
        _ = (skill / "SKILL.md").write_text("---\nname: demo\n---\n# Demo\n", encoding="utf-8")
        curated = skill / "references" / "basics.md"
        _ = curated.write_text(
            "# Demo — Basics\n\n- **Version:** 1.0\n- **Date:** 2026-01-01\n"
            "- **Source:** https://example.com\n- **Brief:** basics.\n",
            encoding="utf-8",
        )
        _ = (skill / "references" / "demo-raw" / "docs" / "intro.md").write_text(
            "# Intro\n\nOld upstream text.\n", encoding="utf-8"
        )
        _ = (skill / "structure-report.json").write_text('{"total_files": 1}\n', encoding="utf-8")
        return skill

    @pytest.fixture
    def new_docs(self, tmp_path: Path) -> Path:
        docs = tmp_path / "new-docs" / "guide"
        docs.mkdir(parents=True)
        _ = (docs / "api.md").write_text("# API\n\nNew functions live here.\n", encoding="utf-8")
        return docs.parent

    def test_stages_update_and_preserves_curated(
        self, existing_skill: Path, new_docs: Path
    ) -> None:
        curated_before = (existing_skill / "references" / "basics.md").read_bytes()
        code = run_to_skill(
            inputs=[str(new_docs)],
            name=None,
            supplementary=[],
            output_dir=None,
            fold_into=existing_skill,
        )
        assert code == 0
        assert (existing_skill / "UPDATE-BRIEF.md").is_file()
        assert (existing_skill / "structure-report-new.json").is_file()
        assert (
            existing_skill / "references" / "demo-raw" / "new-docs" / "guide" / "api.md"
        ).is_file()
        assert (existing_skill / "references" / "basics.md").read_bytes() == curated_before

    def test_update_brief_carries_merge_rules(self, existing_skill: Path, new_docs: Path) -> None:
        _ = run_to_skill(
            inputs=[str(new_docs)],
            name=None,
            supplementary=[],
            output_dir=None,
            fold_into=existing_skill,
        )
        brief = (existing_skill / "UPDATE-BRIEF.md").read_text(encoding="utf-8")
        assert "Existing curated content wins" in brief
        assert "compile.py validate-skill" in brief

    def test_original_structure_report_preserved(
        self, existing_skill: Path, new_docs: Path
    ) -> None:
        _ = run_to_skill(
            inputs=[str(new_docs)],
            name=None,
            supplementary=[],
            output_dir=None,
            fold_into=existing_skill,
        )
        report = (existing_skill / "structure-report.json").read_text(encoding="utf-8")
        assert report == '{"total_files": 1}\n'

    def test_refuses_non_skill_target(self, new_docs: Path, tmp_path: Path) -> None:
        empty = tmp_path / "not-a-skill"
        empty.mkdir()
        code = run_to_skill(
            inputs=[str(new_docs)],
            name=None,
            supplementary=[],
            output_dir=None,
            fold_into=empty,
        )
        assert code == 1
