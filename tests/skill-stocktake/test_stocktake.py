#!/usr/bin/env python3
"""Unit tests for stocktake.py utility functions."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

# Import from global skills directory
import sys
sys.path.insert(0, str(Path.home() / ".claude" / "skills" / "skill-stocktake" / "scripts"))
from stocktake import (
    extract_frontmatter,
    get_mtime_utc,
    _format_path_with_tilde,
    normalize_skills,
    get_skill_name,
    truncate_text,
)


class TestExtractFrontmatter:
    """Tests for extract_frontmatter function."""

    def test_empty_content(self) -> None:
        """Empty content returns empty dict."""
        assert extract_frontmatter("") == {}

    def test_no_frontmatter(self) -> None:
        """Content without frontmatter returns empty dict."""
        content = "# Title\n\nSome content"
        assert extract_frontmatter(content) == {}

    def test_empty_frontmatter(self) -> None:
        """Empty frontmatter block returns empty dict."""
        content = "---\n---\n# Content"
        assert extract_frontmatter(content) == {}

    def test_single_field(self) -> None:
        """Single YAML field is extracted."""
        content = "---\nname: my-skill\n---\n# Content"
        assert extract_frontmatter(content) == {"name": "my-skill"}

    def test_multiple_fields(self) -> None:
        """Multiple YAML fields are extracted."""
        content = "---\nname: my-skill\ndescription: A test skill\n---\n# Content"
        assert extract_frontmatter(content) == {
            "name": "my-skill",
            "description": "A test skill",
        }

    def test_quoted_values(self) -> None:
        """Quoted values are unquoted."""
        content = "---\nname: \"my-skill\"\ndescription: 'A skill'\n---\n# Content"
        assert extract_frontmatter(content) == {
            "name": "my-skill",
            "description": "A skill",
        }

    def test_value_with_colon(self) -> None:
        """Values containing colons are handled."""
        content = "---\ndescription: \"URL: https://example.com\"\n---\n# Content"
        assert extract_frontmatter(content) == {
            "description": "URL: https://example.com",
        }


class TestGetMtimeUtc:
    """Tests for get_mtime_utc function."""

    def test_returns_iso_format(self, tmp_path: Path) -> None:
        """Returns ISO 8601 UTC format string."""
        test_file = tmp_path / "test.md"
        test_file.write_text("content")

        result = get_mtime_utc(test_file)

        # Should be parseable as ISO format
        parsed = datetime.fromisoformat(result.replace("Z", "+00:00"))
        assert parsed.tzinfo is not None

    def test_ends_with_z(self, tmp_path: Path) -> None:
        """Result ends with Z for UTC."""
        test_file = tmp_path / "test.md"
        test_file.write_text("content")

        result = get_mtime_utc(test_file)
        assert result.endswith("Z")


class TestFormatPathWithTilde:
    """Tests for _format_path_with_tilde function."""

    def test_home_path_gets_tilde(self) -> None:
        """Path under home directory gets tilde prefix."""
        home = Path.home()
        test_path = home / ".claude" / "skills" / "test" / "SKILL.md"

        result = _format_path_with_tilde(test_path)

        assert result.startswith("~")
        assert ".claude/skills/test/SKILL.md" in result

    def test_non_home_path_unchanged(self) -> None:
        """Path not under home directory is returned as-is."""
        test_path = Path("/tmp/test/SKILL.md")

        result = _format_path_with_tilde(test_path)

        assert result == str(test_path)

    def test_string_input(self) -> None:
        """Function accepts string input."""
        home = Path.home()
        test_path = str(home / ".claude" / "test.md")

        result = _format_path_with_tilde(test_path)

        assert result.startswith("~")


class TestNormalizeSkills:
    """Tests for normalize_skills helper function."""

    def test_list_passthrough(self) -> None:
        """List input is returned unchanged."""
        skills = [{"path": "~/a", "name": "a"}]
        assert normalize_skills(skills) == skills

    def test_dict_to_list(self) -> None:
        """Dict input is converted to list with path key."""
        skills_dict = {
            "~/skills/a/SKILL.md": {"name": "a", "verdict": "Keep"},
            "~/skills/b/SKILL.md": {"name": "b", "verdict": "Retire"},
        }

        result = normalize_skills(skills_dict)

        assert len(result) == 2
        assert {"path": "~/skills/a/SKILL.md", "name": "a", "verdict": "Keep"} in result
        assert {"path": "~/skills/b/SKILL.md", "name": "b", "verdict": "Retire"} in result

    def test_empty_dict(self) -> None:
        """Empty dict returns empty list."""
        assert normalize_skills({}) == []

    def test_empty_list(self) -> None:
        """Empty list returns empty list."""
        assert normalize_skills([]) == []


class TestGetSkillName:
    """Tests for get_skill_name helper function."""

    def test_name_present(self) -> None:
        """Returns name if present."""
        skill = {"name": "my-skill", "path": "~/skills/other/SKILL.md"}
        assert get_skill_name(skill) == "my-skill"

    def test_name_fallback_to_path(self) -> None:
        """Falls back to path stem if name missing."""
        skill = {"path": "~/skills/my-skill/SKILL.md"}
        assert get_skill_name(skill) == "my-skill"

    def test_name_empty_string_fallback(self) -> None:
        """Falls back if name is empty string."""
        skill = {"name": "", "path": "~/skills/real-name/SKILL.md"}
        assert get_skill_name(skill) == "real-name"

    def test_missing_path(self) -> None:
        """Handles missing path gracefully."""
        skill = {"name": "only-name"}
        assert get_skill_name(skill) == "only-name"


class TestTruncateText:
    """Tests for truncate_text helper function."""

    def test_short_text_unchanged(self) -> None:
        """Text shorter than width is unchanged."""
        assert truncate_text("hello", 10) == "hello"

    def test_exact_width_unchanged(self) -> None:
        """Text exactly at width is unchanged."""
        assert truncate_text("hello", 5) == "hello"

    def test_long_text_truncated(self) -> None:
        """Text longer than width is truncated with ellipsis."""
        result = truncate_text("hello world", 8)
        assert result == "hello w…"
        assert len(result) == 8

    def test_custom_ellipsis(self) -> None:
        """Custom ellipsis character is used."""
        result = truncate_text("hello world", 8, ellipsis="...")
        assert result == "hello..."
        assert len(result) == 8

    def test_zero_width(self) -> None:
        """Zero width returns just ellipsis."""
        # Edge case: width 0 or 1
        result = truncate_text("hello", 1)
        assert result == "…"

    def test_unicode_ellipsis(self) -> None:
        """Unicode ellipsis is single character."""
        result = truncate_text("hello world", 8, ellipsis="…")
        assert result == "hello w…"
        assert len(result) == 8


class TestObservationCounting:
    """Tests for count_read_observations function (integration)."""

    def test_counts_read_tools(self, tmp_path: Path) -> None:
        """Counts only Read tool observations."""
        obs_file = tmp_path / "observations.jsonl"

        # Create observations
        now = datetime.now(UTC)
        ts = now.strftime("%Y-%m-%dT%H:%M:%SZ")

        lines = [
            json.dumps({"tool": "Read", "timestamp": ts, "input": {"file_path": "/a.md"}}),
            json.dumps({"tool": "Write", "timestamp": ts, "input": {"file_path": "/b.md"}}),
            json.dumps({"tool": "Read", "timestamp": ts, "input": {"file_path": "/a.md"}}),
        ]
        obs_file.write_text("\n".join(lines))

        # Import the function
        from stocktake import count_read_observations

        counts_1d, counts_7d, counts_30d = count_read_observations([obs_file])

        # Only Read tools counted, /a.md appears twice
        assert counts_1d.get("/a.md", 0) == 2
        assert counts_1d.get("/b.md", 0) == 0

    def test_counts_all_windows(self, tmp_path: Path) -> None:
        """Counts observations in all time windows."""
        from stocktake import count_read_observations

        obs_file = tmp_path / "observations.jsonl"
        now = datetime.now(UTC)

        # Create timestamps for different windows
        ts_1d = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        ts_7d = (now.replace(day=now.day - 5)).strftime("%Y-%m-%dT%H:%M:%SZ") if now.day > 5 else now.strftime("%Y-%m-%dT%H:%M:%SZ")

        lines = [
            json.dumps({"tool": "Read", "timestamp": ts_1d, "input": {"file_path": "/recent.md"}}),
        ]
        obs_file.write_text("\n".join(lines))

        counts_1d, counts_7d, counts_30d = count_read_observations([obs_file])

        # Recent file should appear in all windows
        assert counts_1d.get("/recent.md", 0) == 1
        assert counts_7d.get("/recent.md", 0) == 1
        assert counts_30d.get("/recent.md", 0) == 1


# Fixtures
@pytest.fixture
def temp_skills_dir(tmp_path: Path) -> Path:
    """Create a temporary skills directory with test skills."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    # Create test skill
    skill_a = skills_dir / "skill-a"
    skill_a.mkdir()
    (skill_a / "SKILL.md").write_text("---\nname: skill-a\ndescription: Test skill A\n---\n# Content")

    # Create another skill
    skill_b = skills_dir / "skill-b"
    skill_b.mkdir()
    (skill_b / "SKILL.md").write_text("---\nname: skill-b\ndescription: Test skill B\n---\n# Content")

    return skills_dir
