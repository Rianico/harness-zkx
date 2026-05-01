"""Tests for skill-stocktake refactoring.

These tests define the expected behavior after refactoring.
They are designed to FAIL against the current implementation.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from pathlib import Path

import pytest


# =============================================================================
# Test 1: Single-Pass Observation Counting
# =============================================================================


@pytest.fixture
def observations_file(tmp_path: Path) -> Path:
    """Create a temporary observations.jsonl with entries spanning 45 days."""
    obs_file = tmp_path / "observations.jsonl"
    now = datetime.now(timezone.utc)

    entries = []
    # 10 entries in last 7 days
    for i in range(10):
        ts = now - timedelta(days=i)
        entries.append({
            "tool": "Read",
            "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "input": {"file_path": f"/path/to/skill_{i % 3}.md"},
        })

    # 15 entries in 8-30 days
    for i in range(15):
        ts = now - timedelta(days=8 + i)
        entries.append({
            "tool": "Read",
            "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "input": {"file_path": f"/path/to/old_skill_{i % 2}.md"},
        })

    # 10 entries in 31-45 days (outside 30d window)
    for i in range(10):
        ts = now - timedelta(days=31 + i)
        entries.append({
            "tool": "Read",
            "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "input": {"file_path": "/path/to/ancient.md"},
        })

    # 5 non-Read tool entries (should be filtered)
    for i in range(5):
        ts = now - timedelta(days=1)
        entries.append({
            "tool": "Write",
            "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "input": {"file_path": "/path/to/other.md"},
        })

    with open(obs_file, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")

    return obs_file


class TestSinglePassObservationCounting:
    """Test that count_read_observations returns both 7d and 30d counts in single pass."""

    def test_count_read_observations_single_pass_returns_tuple(
        self, observations_file: Path
    ) -> None:
        """Function should return tuple of (dict_7d, dict_30d)."""
        from stocktake import count_read_observations

        result = count_read_observations([observations_file])

        # After refactoring, this should return a tuple
        assert isinstance(result, tuple), (
            f"Expected tuple, got {type(result)}. "
            "count_read_observations should return (counts_7d, counts_30d) in single pass."
        )

    def test_count_read_observations_7d_counts(
        self, observations_file: Path
    ) -> None:
        """7d dict should contain only entries from last 7 days."""
        from stocktake import count_read_observations

        result = count_read_observations([observations_file])

        if isinstance(result, tuple):
            counts_7d, counts_30d = result
        else:
            pytest.skip("Function not yet refactored to return tuple")

        # Should have counts for skill_0, skill_1, skill_2 (from 7d window)
        assert len(counts_7d) == 3
        # Each skill appears multiple times in 7d window
        assert counts_7d.get("/path/to/skill_0.md", 0) > 0
        assert counts_7d.get("/path/to/skill_1.md", 0) > 0
        assert counts_7d.get("/path/to/skill_2.md", 0) > 0
        # Ancient should not be in 7d
        assert "/path/to/ancient.md" not in counts_7d

    def test_count_read_observations_30d_superset(
        self, observations_file: Path
    ) -> None:
        """30d dict should be superset of 7d (includes 7d + 8-30d)."""
        from stocktake import count_read_observations

        result = count_read_observations([observations_file])

        if isinstance(result, tuple):
            counts_7d, counts_30d = result
        else:
            pytest.skip("Function not yet refactored to return tuple")

        # 30d should have more skills than 7d
        assert len(counts_30d) > len(counts_7d)
        # 30d should include old_skill entries
        assert any("old_skill" in k for k in counts_30d)
        # But not ancient (31-45 days)
        assert "/path/to/ancient.md" not in counts_30d

    def test_count_read_observations_single_file_open(
        self, observations_file: Path, monkeypatch
    ) -> None:
        """File should be opened only once (single-pass implementation)."""
        from stocktake import count_read_observations
        import stocktake

        # Track open calls
        open_call_count = [0]
        original_open = open

        def tracking_open(*args, **kwargs):
            # Only count opens for our test file
            if len(args) > 0 and str(observations_file) in str(args[0]):
                open_call_count[0] += 1
            return original_open(*args, **kwargs)

        monkeypatch.setattr("builtins.open", tracking_open)

        result = count_read_observations([observations_file])

        if isinstance(result, tuple):
            # File should be opened exactly once for single-pass
            assert open_call_count[0] == 1, (
                f"File opened {open_call_count[0]} times. "
                "Single-pass should open file only once."
            )

    def test_empty_observations_file(self, tmp_path: Path) -> None:
        """Empty observation file returns two empty dicts."""
        from stocktake import count_read_observations

        empty_file = tmp_path / "empty.jsonl"
        empty_file.write_text("")

        result = count_read_observations([empty_file])

        if isinstance(result, tuple):
            counts_7d, counts_30d = result
            assert counts_7d == {}
            assert counts_30d == {}

    def test_malformed_json_lines_skipped(self, tmp_path: Path) -> None:
        """Malformed JSON lines are skipped, valid lines still counted."""
        from stocktake import count_read_observations

        obs_file = tmp_path / "mixed.jsonl"
        now = datetime.now(timezone.utc)

        lines = [
            "this is not json",
            json.dumps({
                "tool": "Read",
                "timestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "input": {"file_path": "/valid/path.md"},
            }),
            "{broken json",
            json.dumps({
                "tool": "Read",
                "timestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "input": {"file_path": "/another/valid.md"},
            }),
        ]
        obs_file.write_text("\n".join(lines))

        result = count_read_observations([obs_file])

        if isinstance(result, tuple):
            counts_7d, counts_30d = result
            assert len(counts_7d) == 2
            assert "/valid/path.md" in counts_7d
            assert "/another/valid.md" in counts_7d


# =============================================================================
# Test 2: Verdict StrEnum Type Safety
# =============================================================================


class TestVerdictEnum:
    """Test that Verdict is a proper StrEnum with expected values."""

    def test_verdict_enum_import(self) -> None:
        """Verdict enum should be importable from stocktake module."""
        from stocktake import Verdict

        assert Verdict is not None

    def test_verdict_enum_is_strenum(self) -> None:
        """Verdict should be instance of StrEnum."""
        from stocktake import Verdict

        assert issubclass(Verdict, StrEnum), (
            f"Verdict should be a StrEnum, got {type(Verdict)}"
        )

    def test_verdict_enum_values(self) -> None:
        """Verdict enum should have correct string values."""
        from stocktake import Verdict

        assert Verdict.KEEP.value == "Keep"
        assert Verdict.IMPROVE.value == "Improve"
        assert Verdict.UPDATE.value == "Update"
        assert Verdict.MERGE.value == "Merge"
        assert Verdict.RETIRE.value == "Retire"

    def test_verdict_string_lookup(self) -> None:
        """Verdict members should be accessible via string lookup."""
        from stocktake import Verdict

        assert Verdict("Keep") == Verdict.KEEP
        assert Verdict("Improve") == Verdict.IMPROVE
        assert Verdict("Update") == Verdict.UPDATE
        assert Verdict("Merge") == Verdict.MERGE
        assert Verdict("Retire") == Verdict.RETIRE

    def test_verdict_all_members(self) -> None:
        """Verdict should have exactly 5 members."""
        from stocktake import Verdict

        members = list(Verdict)
        assert len(members) == 5
        assert set(members) == {
            Verdict.KEEP,
            Verdict.IMPROVE,
            Verdict.UPDATE,
            Verdict.MERGE,
            Verdict.RETIRE,
        }


# =============================================================================
# Test 3: Path Formatting Utility
# =============================================================================


class TestFormatPathWithTilde:
    """Test the extracted _format_path_with_tilde utility."""

    def test_format_path_with_tilde_home_path(self, monkeypatch) -> None:
        """Paths under home directory should use tilde prefix."""
        from stocktake import _format_path_with_tilde

        monkeypatch.setattr(Path, "home", lambda: Path("/home/testuser"))

        result = _format_path_with_tilde(Path("/home/testuser/.claude/skills/foo"))
        assert result == "~/.claude/skills/foo"

    def test_format_path_with_tilde_nested_file(self, monkeypatch) -> None:
        """Nested files under home should preserve full relative path."""
        from stocktake import _format_path_with_tilde

        monkeypatch.setattr(Path, "home", lambda: Path("/home/testuser"))

        result = _format_path_with_tilde(
            Path("/home/testuser/.claude/skills/foo/bar.md")
        )
        assert result == "~/.claude/skills/foo/bar.md"

    def test_format_path_with_tilde_non_home_path(self, monkeypatch) -> None:
        """Paths outside home directory should remain unchanged."""
        from stocktake import _format_path_with_tilde

        monkeypatch.setattr(Path, "home", lambda: Path("/home/testuser"))

        result = _format_path_with_tilde(Path("/other/path/file.md"))
        assert result == "/other/path/file.md"

    def test_format_path_with_tilde_relative_path(self, monkeypatch) -> None:
        """Relative paths should remain unchanged."""
        from stocktake import _format_path_with_tilde

        monkeypatch.setattr(Path, "home", lambda: Path("/home/testuser"))

        result = _format_path_with_tilde(Path("relative/path.md"))
        assert result == "relative/path.md"

    def test_format_path_with_tilde_returns_string(self, monkeypatch) -> None:
        """Function should return string, not Path object."""
        from stocktake import _format_path_with_tilde

        monkeypatch.setattr(Path, "home", lambda: Path("/home/testuser"))

        result = _format_path_with_tilde(Path("/home/testuser/test.md"))
        assert isinstance(result, str)

    def test_format_path_with_tilde_exact_home(self, monkeypatch) -> None:
        """Path exactly equal to home should return just tilde."""
        from stocktake import _format_path_with_tilde

        monkeypatch.setattr(Path, "home", lambda: Path("/home/testuser"))

        result = _format_path_with_tilde(Path("/home/testuser"))
        assert result == "~"

    def test_format_path_with_tilde_string_input(self, monkeypatch) -> None:
        """Function should handle string input as well as Path."""
        from stocktake import _format_path_with_tilde

        monkeypatch.setattr(Path, "home", lambda: Path("/home/testuser"))

        result = _format_path_with_tilde("/home/testuser/.claude/skills/test.md")
        assert result == "~/.claude/skills/test.md"


# =============================================================================
# Test 4: Directory Walking Utility
# =============================================================================


@pytest.fixture
def skills_dir(tmp_path: Path) -> Path:
    """Create a temporary skills directory with realistic structure."""
    skills = tmp_path / "skills"
    skills.mkdir()

    # skill-a/SKILL.md
    skill_a = skills / "skill-a"
    skill_a.mkdir()
    (skill_a / "SKILL.md").write_text("---\nname: skill-a\n---\nContent")

    # skill-b/SKILL.md and sub.md
    skill_b = skills / "skill-b"
    skill_b.mkdir()
    (skill_b / "SKILL.md").write_text("---\nname: skill-b\n---\nContent")
    (skill_b / "sub.md").write_text("Sub content")

    # not-skill.txt (should be skipped)
    (skills / "not-skill.txt").write_text("Not a skill")

    # deep/nested/SKILL.md
    deep = skills / "deep" / "nested"
    deep.mkdir(parents=True)
    (deep / "SKILL.md").write_text("---\nname: deep-skill\n---\nContent")

    return skills


class TestWalkSkillsDir:
    """Test the extracted _walk_skills_dir utility."""

    def test_walk_skills_dir_returns_generator(self, skills_dir: Path) -> None:
        """Function should return generator/iterator of Path objects."""
        from stocktake import _walk_skills_dir

        result = _walk_skills_dir(skills_dir)
        assert hasattr(result, "__iter__"), "Should return iterable"
        # Collect to verify
        paths = list(result)
        assert all(isinstance(p, Path) for p in paths)

    def test_walk_skills_dir_only_md_files(self, skills_dir: Path) -> None:
        """Should yield only .md files."""
        from stocktake import _walk_skills_dir

        paths = list(_walk_skills_dir(skills_dir))
        assert all(p.suffix == ".md" for p in paths)

    def test_walk_skills_dir_skips_non_markdown(self, skills_dir: Path) -> None:
        """Should skip non-markdown files."""
        from stocktake import _walk_skills_dir

        paths = list(_walk_skills_dir(skills_dir))
        path_strs = [str(p) for p in paths]
        assert not any("not-skill.txt" in p for p in path_strs)

    def test_walk_skills_dir_recurse_subdirectories(self, skills_dir: Path) -> None:
        """Should recurse into subdirectories."""
        from stocktake import _walk_skills_dir

        paths = list(_walk_skills_dir(skills_dir))
        path_strs = [str(p) for p in paths]

        # Should find nested skill
        assert any("deep" in p and "nested" in p for p in path_strs)
        assert any("SKILL.md" in p for p in path_strs)

    def test_walk_skills_dir_handles_empty(self, tmp_path: Path) -> None:
        """Should handle empty directories gracefully."""
        from stocktake import _walk_skills_dir

        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        paths = list(_walk_skills_dir(empty_dir))
        assert paths == []

    def test_walk_skills_dir_followlinks(self, skills_dir: Path) -> None:
        """Should follow symlinks when followlinks=True."""
        from stocktake import _walk_skills_dir

        # Create a symlinked skill
        linked_skill = skills_dir.parent / "linked-skill"
        linked_skill.mkdir()
        (linked_skill / "LINKED.md").write_text("Linked content")

        # Create symlink
        symlink_dir = skills_dir / "symlinked"
        symlink_dir.symlink_to(linked_skill)

        paths = list(_walk_skills_dir(skills_dir, followlinks=True))
        path_strs = [str(p) for p in paths]

        assert any("LINKED.md" in p for p in path_strs)

    def test_walk_skills_dir_count(self, skills_dir: Path) -> None:
        """Should find expected number of .md files."""
        from stocktake import _walk_skills_dir

        paths = list(_walk_skills_dir(skills_dir))
        # skill-a/SKILL.md, skill-b/SKILL.md, skill-b/sub.md, deep/nested/SKILL.md
        assert len(paths) == 4


# =============================================================================
# Test 5: No Decorative Comment Blocks
# =============================================================================


class TestNoDecorativeComments:
    """Test that decorative comment blocks are removed."""

    def test_no_decorative_dividers(self) -> None:
        """Source should not contain decorative === dividers."""
        import stocktake
        import inspect

        source = inspect.getsource(stocktake)
        lines = source.split("\n")

        for i, line in enumerate(lines, 1):
            # Check for decorative dividers like # ===...
            if line.strip().startswith("#") and "===" in line:
                # Allow if it's a comment with actual content
                content = line.strip().lstrip("#").strip()
                if not content or set(content) == {"="}:
                    pytest.fail(
                        f"Decorative comment block at line {i}: {line!r}"
                    )

    def test_no_empty_comment_blocks(self) -> None:
        """Source should not contain empty comment-only blocks."""
        import stocktake
        import inspect

        source = inspect.getsource(stocktake)
        lines = source.split("\n")

        # Check for consecutive lines that are only "#"
        consecutive_empty_comments = 0
        for line in lines:
            if line.strip() == "#":
                consecutive_empty_comments += 1
            else:
                consecutive_empty_comments = 0

            if consecutive_empty_comments > 1:
                pytest.fail(
                    f"Found empty comment block (consecutive # lines)"
                )
